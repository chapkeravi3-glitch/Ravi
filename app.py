"""app.py - Ravi AI Video Creator (Streamlit ऐप)
हिंदी में टॉपिक या स्क्रिप्ट डालो, आवाज़ + सही फ़ोटो + कैप्शन वाला वीडियो पाओ।
"""
import os
import streamlit as st

st.set_page_config(page_title="Ravi AI Video Creator", page_icon="🎬", layout="centered")

import engine  # noqa: E402

st.title("🎬 Ravi AI Video Creator")
st.caption("हिंदी वीडियो अपने-आप: स्क्रिप्ट + आवाज़ + सही फ़ोटो/क्लिप + कैप्शन")

with st.sidebar:
    st.header("🔑 आपकी Keys")
    gem = st.text_input("Gemini API Key (ज़रूरी, फ्री)", type="password",
                        help="aistudio.google.com/apikey से मुफ़्त मिलती है")
    pix = st.text_input("Pixabay Key (वैकल्पिक)", type="password",
                        help="इसके साथ असली वीडियो क्लिप भी लगेंगी")
    pex = st.text_input("Pexels Key (वैकल्पिक)", type="password")
    use_clip = st.checkbox("सटीक फ़ोटो चुनना (CLIP AI)", value=False,
                           help="ज़्यादा RAM चाहिए। अपने लैपटॉप पर चलाओ तो चालू करो")
    st.caption("आपकी keys सिर्फ़ इसी सेशन में इस्तेमाल होती हैं, कहीं सेव नहीं होतीं।")

kind_label = st.radio("वीडियो का प्रकार", ["शॉर्ट (खड़ा, 9:16)", "लॉन्ग (आड़ा, 16:9)"], horizontal=True)
kind = "short" if kind_label.startswith("शॉर्ट") else "long"
voice_label = st.radio("आवाज़", ["पुरुष", "महिला"], horizontal=True)
captions = st.checkbox("स्क्रीन पर कैप्शन लगाओ", value=True)

tab1, tab2 = st.tabs(["✍️ टॉपिक से", "📝 अपनी स्क्रिप्ट से"])
with tab1:
    topic = st.text_input("टॉपिक", placeholder="जैसे: कुम्भलगढ़ किले की दीवार का रहस्य")
    niche = st.text_input("चैनल किस बारे में है? (वैकल्पिक)", placeholder="जैसे: भारत के रोचक तथ्य")
    go_topic = st.button("🎥 वीडियो बनाओ", key="go1", type="primary")
with tab2:
    text = st.text_area("अपनी हिंदी स्क्रिप्ट यहाँ चिपकाओ", height=220)
    go_text = st.button("🎥 वीडियो बनाओ", key="go2", type="primary")


def run(make_script):
    if not gem.strip():
        st.error("बाईं तरफ़ (या ऊपर ☰ मेन्यू में) Gemini API Key डालो।")
        return
    os.environ["GEMINI_API_KEY"] = gem.strip()
    os.environ["PIXABAY_API_KEY"] = pix.strip()
    os.environ["PEXELS_API_KEY"] = pex.strip()
    os.environ["USE_CLIP"] = "1" if use_clip else "0"
    bar = st.progress(0.0, text="स्क्रिप्ट बन रही है...")
    try:
        script = make_script()
        bar.progress(0.05, text=f"स्क्रिप्ट तैयार: {script['title']}")

        def progress(i, n, msg):
            bar.progress(min(0.05 + 0.95 * i / max(n, 1), 1.0), text=msg)

        res = engine.render_video(script, kind, voice_label == "पुरुष", captions, progress)
        st.session_state["result"] = {
            "script": script,
            "video": res["video"].read_bytes(),
            "thumb": res["thumb"].read_bytes() if res["thumb"] else None,
            "credits": res["credits"],
        }
        bar.empty()
    except Exception as e:
        bar.empty()
        st.error(f"कुछ गड़बड़ हुई: {e}")


if go_topic:
    if not topic.strip():
        st.warning("पहले टॉपिक लिखो।")
    else:
        run(lambda: engine.script_from_topic(topic.strip(), niche.strip(), kind))
if go_text:
    if len(text.strip()) < 50:
        st.warning("स्क्रिप्ट थोड़ी लंबी चिपकाओ।")
    else:
        run(lambda: engine.script_from_text(text.strip(), kind))

r = st.session_state.get("result")
if r:
    s = r["script"]
    st.success("✅ वीडियो तैयार है!")
    st.video(r["video"])
    st.download_button("⬇️ वीडियो डाउनलोड करो (MP4)", r["video"], file_name="video.mp4",
                       mime="video/mp4")
    if r["thumb"]:
        st.image(r["thumb"], caption="थंबनेल")
        st.download_button("⬇️ थंबनेल डाउनलोड करो", r["thumb"], file_name="thumbnail.jpg",
                           mime="image/jpeg")
    st.subheader("यूट्यूब के लिए")
    st.text_input("टाइटल", s["title"])
    desc = s.get("description", "") + "\n\n" + " ".join(s.get("hashtags", []))
    if r["credits"]:
        desc += "\n\nफ़ोटो/वीडियो क्रेडिट:\n" + "\n".join(r["credits"])
    st.text_area("डिस्क्रिप्शन (क्रेडिट समेत, इसे ज़रूर चिपकाओ)", desc, height=200)
    st.text_input("टैग", ", ".join(map(str, s.get("tags", []))))
