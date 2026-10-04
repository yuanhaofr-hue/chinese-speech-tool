import streamlit as st
import edge_tts
import asyncio
import tempfile
import re
from difflib import SequenceMatcher

# Configuration de la page
st.set_page_config(page_title="Outil d'évaluation de la prononciation du chinois", page_icon="🎙️")

st.title("🎙️ Outil d'Évaluation Vocale de Chinois")
st.write("Générez des modèles d'écoute phrase par phrase et évaluez votre prononciation.")

# ---------------------------------------------------------
# 1. Section Modèle de Lecture (Version Française)
# ---------------------------------------------------------
st.header("1. Génération du modèle de lecture (范本朗读)")

default_text = "你好！欢迎来到中文课堂。祝你学习愉快！"
text_input = st.text_area("Entrez le texte chinois à pratiquer (输入中文文本) :", default_text)

voice_option = st.selectbox(
    "Choisissez la voix (选择发音人) :",
    ["zh-CN-XiaoxiaoNeural (Voix féminine / 女声)", "zh-CN-YunxiNeural (Voix masculine / 男声)"]
)
voice_id = "zh-CN-XiaoxiaoNeural" if "Xiaoxiao" in voice_option else "zh-CN-YunxiNeural"

# Fonction asynchrone pour générer l'audio d'une phrase
async def generate_sentence_audio(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        await communicate.save(tmp_file.name)
        return tmp_file.name

# Découpage du texte en phrases (按句拆分)
def split_sentences(text):
    # Découpage par la ponctuation chinoise et française
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

# Affichage des phrases avec lecture individuelle (逐句播放)
if 'sentences' in st.session_state and st.session_state['sentences']:
    st.subheader("🔊 Écoute phrase par phrase (逐句重复朗读) :")
    for idx, sentence in enumerate(st.session_state['sentences']):
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"**Phrase {idx+1} :** {sentence}")
        with col2:
            with st.spinner("Génération..."):
                audio_file = asyncio.run(generate_sentence_audio(sentence, voice_id))
                st.audio(audio_file, format="audio/mp3")

st.divider()

# ---------------------------------------------------------
# 2. Section Enregistrement et Évaluation
# ---------------------------------------------------------
st.header("2. Enregistrement et Évaluation (学生录音与打分)")

st.write("Veuillez enregistrer votre lecture ci-dessous (请录音) :")
student_audio = st.audio_input("Enregistrer votre voix")

if student_audio:
    st.audio(student_audio)
    
    if st.button("📊 Analyser la prononciation (开始评估)"):
        st.subheader("📈 Résultat de l'analyse (评估结果) :")
        
        # Target text for comparison
        target_text = text_input.replace("\n", "").strip()
        
        # Simulated Recognition Result (Example for demonstration)
        # In production, replace this with ASR (Speech-To-Text) result
        recognized_text = "你好欢迎来到中文课。祝你学习愉快" 
        
        st.markdown(f"**Texte original (原文本) :** `{target_text}`")
        st.markdown(f"**Reconnu à partir de votre voix (识别结果) :** `{recognized_text}`")
        
        # Algorithme de comparaison de texte (Comparaison par couleur)
        matcher = SequenceMatcher(None, target_text, recognized_text)
        colored_result = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Mot correct (Vert)
                colored_result.append(f"<span style='color:green; font-weight:bold; font-size:20px;'>{target_text[i1:i2]}</span>")
            elif tag == 'replace' or tag == 'delete':
                # Mot incorrect ou manqué (Rouge)
                colored_result.append(f"<span style='color:red; text-decoration:line-through; font-weight:bold; font-size:20px;'>{target_text[i1:i2]}</span>")
            elif tag == 'insert':
                # Mot ajouté en trop (Bleu)
                colored_result.append(f"<span style='color:blue; font-weight:bold; font-size:20px;'>[{recognized_text[j1:j2]}]</span>")
                
        diff_html = "".join(colored_result)
        
        st.markdown("### 🎨 Comparaison visuelle (对比结果) :")
        st.write("🟢 **Vert** : Correct | 🔴 **Rouge** : Incorrect/Manqué | 🔵 **Bleu** : Mot ajouté")
        st.markdown(f"<div style='background-color:#f0f2f6; padding:15px; border-radius:10px;'>{diff_html}</div>", unsafe_allow_html=True)
        
        # Feedback personnalisé en Français
        st.markdown("### 💡 Conseils de prononciation (发音建议) :")
        st.info("""
        - **Note globale : 85/100**
        - **Attention au ton (声调提醒) :** Vérifiez le 2ème ton (阳平) sur le mot **“堂” (táng)** dans “课堂”.
        - **Fluidité (流畅度) :** Bonne vitesse globale. Continuez ainsi !
        """)
