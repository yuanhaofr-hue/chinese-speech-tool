import streamlit as st
import edge_tts
import asyncio
import tempfile
import re
import os
import whisper
from difflib import SequenceMatcher

# Configuration de la page
st.set_page_config(page_title="Outil d'évaluation du chinois", page_icon="🎙️")

st.title("🎙️ Outil d'Évaluation Vocale de Chinois")
st.write("Entraînez-vous phrase par phrase, vérifiez votre prononciation et validez vos résultats !")

# Charger le modèle Whisper (Reconnaissance vocale)
@st.cache_resource
def load_whisper_model():
    # Modèle 'tiny' ou 'base' : très rapide et parfait pour les serveurs gratuits
    return whisper.load_model("base")

whisper_model = load_whisper_model()

# ---------------------------------------------------------
# 1. Section Modèle de Lecture (avec contrôle de vitesse)
# ---------------------------------------------------------
st.header("1. Modèle de lecture (范本朗读)")

default_text = "你好！欢迎来到中文课堂。祝你学习愉快！"
text_input = st.text_area("Entrez le texte chinois à pratiquer (输入中文文本) :", default_text)

col_voice, col_speed = st.columns(2)
with col_voice:
    voice_option = st.selectbox(
        "Voix (发音人) :",
        ["zh-CN-XiaoxiaoNeural (Femme)", "zh-CN-YunxiNeural (Homme)"]
    )
    voice_id = "zh-CN-XiaoxiaoNeural" if "Xiaoxiao" in voice_option else "zh-CN-YunxiNeural"

with col_speed:
    # 语速调节 (0.5, 0.75, 1.0, 1.25, 1.5)
    speed_factor = st.select_slider(
        "Vitesse de lecture (朗读语速) :",
        options=[0.5, 0.75, 1.0, 1.25, 1.5],
        value=1.0,
        format_func=lambda x: f"{x}x"
    )

# Transfert du facteur numérique vers le format attendu par Edge-TTS (ex: "-25%", "+0%", "+25%")
def get_rate_str(factor):
    percentage = int((factor - 1.0) * 100)
    if percentage >= 0:
        return f"+{percentage}%"
    else:
        return f"{percentage}%"

# Synthèse vocale asynchrone
async def generate_sentence_audio(text, voice, rate_str):
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        await communicate.save(tmp_file.name)
        return tmp_file.name

def split_sentences(text):
    sentences = re.split(r'([。？！；?!;\n]+)', text)
    result = []
    for i in range(0, len(sentences)-1, 2):
        s = sentences[i].strip() + sentences[i+1].strip()
        if s.strip():
            result.append(s)
    if len(sentences) % 2 != 0 and sentences[-1].strip():
        result.append(sentences[-1].strip())
    return [s for s in result if s]

if st.button("🔊 Générer l'audio par phrase (按句生成音频)"):
    if text_input.strip():
        sentences = split_sentences(text_input)
        st.session_state['sentences'] = sentences
        st.success(f"Texte divisé en {len(sentences)} phrase(s) !")
    else:
        st.warning("Veuillez entrer un texte valide.")

if 'sentences' in st.session_state and st.session_state['sentences']:
    st.subheader("🔊 Écoute phrase par phrase (逐句重复朗读) :")
    rate_str = get_rate_str(speed_factor)
    for idx, sentence in enumerate(st.session_state['sentences']):
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"**Phrase {idx+1} :** {sentence}")
        with col2:
            with st.spinner("Génération..."):
                audio_file = asyncio.run(generate_sentence_audio(sentence, voice_id, rate_str))
                st.audio(audio_file, format="audio/mp3")

st.divider()

# ---------------------------------------------------------
# 2. Section Enregistrement, Transcriptions & Comparaison
# ---------------------------------------------------------
st.header("2. Enregistrement & Analyse de la prononciation (录音与对比)")

st.write("Veuillez enregistrer votre lecture (录制你的发音) :")
student_audio = st.audio_input("Enregistrer votre voix")

if student_audio:
    st.audio(student_audio)
    
    if st.button("📊 Transcrire et évaluer (转写与打分)"):
        with st.spinner("Reconnaissance vocale en cours (正在转写录音...)"):
            # Enregistrer temporairement l'audio de l'élève
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                tmp_audio.write(student_audio.getvalue())
                tmp_audio_path = tmp_audio.name

            # Transcription avec Whisper (Force le chinois)
            result = whisper_model.transcribe(tmp_audio_path, language="zh")
            recognized_text = result["text"].strip()
            os.remove(tmp_audio_path)  # Nettoyage
        
        # Nettoyage des chaînes pour la comparaison (Suppression des ponctuations)
        clean_target = re.sub(r'[^\w\s]', '', text_input.replace("\n", "").strip())
        clean_recognized = re.sub(r'[^\w\s]', '', recognized_text)

        # Calcul du score sur 100%
        matcher = SequenceMatcher(None, clean_target, clean_recognized)
        similarity = matcher.ratio()
        score = int(similarity * 100)

        st.subheader("📈 Résultat de l'analyse (评估结果) :")
        
        # Affichage du score principal
        st.metric(label="Score de précision (发音准确度得分)", value=f"{score} / 100")
        
        # Transcriptions
        st.markdown(f"**Texte attendu (标准范文) :** `{text_input.strip()}`")
        st.markdown(f"**Ce que nous avons entendu (学生实际读出) :** `{recognized_text if recognized_text else '(Aucune parole détectée)'}`")

        # Comparaison mot à mot avec couleurs
        colored_result = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                colored_result.append(f"<span style='color:green; font-weight:bold; font-size:22px;'>{clean_target[i1:i2]}</span>")
            elif tag in ('replace', 'delete'):
                colored_result.append(f"<span style='color:red; text-decoration:line-through; font-weight:bold; font-size:22px;'>{clean_target[i1:i2]}</span>")
            elif tag == 'insert':
                colored_result.append(f"<span style='color:blue; font-weight:bold; font-size:22px;'>[{clean_recognized[j1:j2]}]</span>")

        diff_html = "".join(colored_result)

        st.markdown("### 🎨 Visualisation des erreurs (发音对照) :")
        st.write("🟢 **Vert** : Correctement prononcé | 🔴 **Rouge** : Mal prononcé/Oublié | 🔵 **Bleu** : Mot ajouté")
        st.markdown(f"<div style='background-color:#f0f2f6; padding:15px; border-radius:10px;'>{diff_html}</div>", unsafe_allow_html=True)

        # Section Validation pour l'enseignant
        st.divider()
        st.subheader("📋 Rapport à envoyer à votre professeur (发送给老师的验证报告)")
        
        if score >= 80:
            st.success("🎉 Excellent travail ! Votre score est suffisant pour valider.")
        else:
            st.warning("💡 Continuez à vous entraîner pour améliorer votre score avant d'envoyer le rapport.")

        # Modèle de rapport à copier/coller
        report_text = f"""--- Rapport de Prononciation Chinoise ---
Élève : [Votre Nom]
Texte pratiqué : {text_input.strip()}
Score de précision : {score}/100
Transcription enregistrée : {recognized_text}
Status : {'Validé ✅' if score >= 80 else 'À retravailler 🔄'}
---------------------------------------"""
        
        st.code(report_text, language="text")
        st.caption("Conseil : Copiez ce texte et envoyez-le à votre professeur par e-mail ou sur votre plateforme de cours.")
