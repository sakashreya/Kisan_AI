import re

CODES = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "mr": "mar_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
}
MODELS = {
    "indic-en": "ai4bharat/indictrans2-indic-en-dist-200M",
    "en-indic": "ai4bharat/indictrans2-en-indic-dist-200M",
}
_cache = {}
_ip = None
DEVICE = None


def _get_ip():
    global _ip
    if _ip is None:
        from IndicTransToolkit.processor import IndicProcessor
        _ip = IndicProcessor(inference=True)
    return _ip

# Agronomic terms that are protected from translation drift.
# When translated to regional languages, they are rendered bilingually:
# e.g. மான்கோசெப் (Mancozeb) in Tamil, मॅनकोझेब (Mancozeb) in Marathi,
# allowing the farmer to read it easily while matching the English bottle label at shops.
PROTECTED_TERMS = [
    # Institutions
    "Krishi Vigyan Kendra", "KVK", "ICAR", "TNAU",
    # Biocontrol agents
    "Trichoderma viride", "Trichoderma harzianum", "Pseudomonas fluorescens",
    "Bacillus subtilis", "Beauveria bassiana", "Metarhizium anisopliae",
    "Verticillium lecanii", "Nuclear Polyhedrosis Virus", "NPV",
    # Botanicals
    "Neem Seed Kernel Extract", "NSKE", "Neem oil",
    # Fungicides
    "Copper oxychloride", "Streptocycline", "Hexaconazole", "Propiconazole",
    "Tricyclazole", "Carbendazim", "Mancozeb", "Edifenphos", "Thiram",
    "Captan", "Metalaxyl", "Dinocap", "Wettable sulphur", "Bordeaux mixture",
    "Kasugamycin", "Validamycin", "Chlorothalonil", "Zineb", "Carboxin",
    # Insecticides
    "Chlorpyriphos", "Chlorpyrifos", "Imidacloprid", "Dimethoate", "Malathion",
    "Monocrotophos", "Acephate", "Cypermethrin", "Lambda-cyhalothrin",
    "Thiamethoxam", "Fipronil", "Spinosad", "Cartap hydrochloride",
    "Quinalphos", "Phosphamidon", "Profenofos", "Profenophos", "Novaluron", "Indoxacarb",
    "Flubendiamide", "Chlorantraniliprole", "Emamectin benzoate", "Phorate",
    "Carbofuran", "Dichlorvos", "Endosulfan",
    # Pathogens (scientific names)
    "Xanthomonas oryzae", "Magnaporthe oryzae", "Rhizoctonia solani",
    "Fusarium oxysporum", "Pyricularia oryzae", "Bipolaris oryzae",
    "Sarocladium oryzae", "Ustilaginoidea virens",
    # Disease common names
    "Rice blast", "False smut", "Bacterial leaf blight", "Sheath blight",
    "Stem rot", "Downy mildew", "Powdery mildew", "Leaf spot", "Tikka leaf spot", "Tikka disease", "Wilt",
    # Pest common names
    "Spodoptera litura", "Helicoverpa armigera", "Brown planthopper", "BPH",
    "Yellow stem borer", "Stem borer", "Gall midge", "Leaf folder",
    "Fall armyworm", "Pink bollworm", "Bollworm", "Fruit borer", "Whitefly", "Aphids", "Thrips",
    "Mites", "Root-knot nematode", "Meloidogyne",
]

BILINGUAL_GLOSSARY = {
    "ta": {
        # Institutions
        "krishi vigyan kendra": "வேளாண் அறிவியல் மையம்",
        "kvk": "கே.வி.கே",
        "icar": "ஐ.சி.ஏ.ஆர்",
        "tnau": "டி.என்.ஏ.யு",
        # Biocontrol
        "trichoderma viride": "ட்ரைக்கோடெர்மா விரிடி",
        "trichoderma harzianum": "ட்ரைக்கோடெர்மா ஹார்சியானம்",
        "pseudomonas fluorescens": "சூடோமோனாஸ் ஃப்ளோரசன்ஸ்",
        "bacillus subtilis": "பேசில்லஸ் சப்டிலிஸ்",
        "beauveria bassiana": "பியூவேரியா பேசியானா",
        "metarhizium anisopliae": "மெட்டாரைசியம் அனிசோபிலியே",
        "verticillium lecanii": "வெர்ட்டிசிலியம் லெக்கானி",
        "nuclear polyhedrosis virus": "என்.பி.வி வைரஸ்",
        "npv": "என்.பி.வி",
        # Botanicals
        "neem seed kernel extract": "வேப்பங்கொட்டை சாறு",
        "nske": "வேப்பங்கொட்டை சாறு",
        "neem oil": "வேப்ப எண்ணெய்",
        # Fungicides
        "copper oxychloride": "காப்பர் ஆக்ஸிகுளோரைடு",
        "streptocycline": "ஸ்ட்ரெப்டோசைக்ளின்",
        "hexaconazole": "ஹெக்ஸாகோனசோல்",
        "propiconazole": "புரோபிகோனசோல்",
        "tricyclazole": "ட்ரைசைக்ளசோல்",
        "carbendazim": "கார்பெண்டாசிம்",
        "mancozeb": "மான்கோசெப்",
        "edifenphos": "எடிபென்பாஸ்",
        "thiram": "திராம்",
        "captan": "கேப்டான்",
        "metalaxyl": "மெட்டாலாக்ஸில்",
        "dinocap": "டினோகேப்",
        "wettable sulphur": "நனையும் கந்தகம்",
        "bordeaux mixture": "போர்டோ கலவை",
        "kasugamycin": "கசுகாமைசின்",
        "validamycin": "வாலிடாமைசின்",
        "chlorothalonil": "குளோரோதலோனில்",
        "zineb": "ஜினெப்",
        "carboxin": "கார்பாக்சின்",
        # Insecticides
        "chlorpyriphos": "குளோர்பைரிபாஸ்",
        "chlorpyrifos": "குளோர்பைரிபாஸ்",
        "imidacloprid": "இமிடாக்ளோப்ரிட்",
        "dimethoate": "டைமெத்தோயேட்",
        "malathion": "மலாத்தியான்",
        "monocrotophos": "மோனோகுரோட்டோபாஸ்",
        "acephate": "அசிபேட்",
        "cypermethrin": "சைபர்மெத்ரின்",
        "lambda-cyhalothrin": "லாம்ப்டா-சைஹாலோத்ரின்",
        "thiamethoxam": "தயோமெதோக்சாம்",
        "fipronil": "பிப்ரோனில்",
        "spinosad": "ஸ்பினோசாட்",
        "cartap hydrochloride": "கார்டாப் ஹைட்ரோகுளோரைடு",
        "quinalphos": "குயினால்பாஸ்",
        "phosphamidon": "பாஸ்பாமிடான்",
        "profenofos": "புரோபெனோபாஸ்",
        "profenophos": "புரோபெனோபாஸ்",
        "novaluron": "நோவலுரான்",
        "indoxacarb": "இன்டோக்சாகார்ப்",
        "flubendiamide": "புளூபெண்டியமைடு",
        "chlorantraniliprole": "குளோரான்ட்ரானிலிப்ரோல்",
        "emamectin benzoate": "எமாமெக்டின் பென்சோயேட்",
        "phorate": "போரேட்",
        "carbofuran": "கார்போபியூரான்",
        "dichlorvos": "டைக்ளோர்வோஸ்",
        "endosulfan": "எண்டோசல்பான்",
        # Diseases
        "rice blast": "குலை நோய்",
        "false smut": "மஞ்சள் கதிர் பூஞ்சை",
        "bacterial leaf blight": "பாக்டீரியா இலை கருகல்",
        "sheath blight": "இலை உறை அழுகல்",
        "stem rot": "தண்டு அழுகல்",
        "downy mildew": "அடிச்சாம்பல் நோய்",
        "powdery mildew": "சாம்பல் நோய்",
        "leaf spot": "இலைப்புள்ளி நோய்",
        "tikka leaf spot": "டிக்கா இலைப்புள்ளி நோய்",
        "tikka disease": "டிக்கா நோய்",
        "wilt": "வாடல் நோய்",
        # Pests
        "brown planthopper": "பழுப்பு தத்துப்பூச்சி",
        "bph": "பழுப்பு தத்துப்பூச்சி",
        "yellow stem borer": "மஞ்சள் தண்டு துளைப்பான்",
        "stem borer": "தண்டு துளைப்பான்",
        "gall midge": "ஆனைக்கொம்பன் ஈ",
        "leaf folder": "இலை சுருட்டுப்புழு",
        "fall armyworm": "படைப்புழு",
        "pink bollworm": "இளஞ்சிவப்பு காய்ப்புழு",
        "bollworm": "காய்ப்புழு",
        "fruit borer": "காய்ப்புழு",
        "whitefly": "வெள்ளை ஈ",
        "aphids": "அசுவினி",
        "thrips": "இலைப்பேன்",
        "mites": "செம்பேன்",
        "root-knot nematode": "வேர் முடிச்சு நூற்புழு",
    },
    "mr": {
        # Institutions
        "krishi vigyan kendra": "कृषी विज्ञान केंद्र",
        "kvk": "केव्हीके",
        "icar": "आय.सी.ए.आर",
        "tnau": "टी.एन.ए.यू",
        # Biocontrol
        "trichoderma viride": "ट्रायकोडर्मा व्हिराइड",
        "trichoderma harzianum": "ट्रायकोडर्मा हार्झियानम",
        "pseudomonas fluorescens": "सुडोमोनास फ्लूरोसेन्स",
        "bacillus subtilis": "बॅसिलस सबटिलिस",
        "beauveria bassiana": "ब्यूव्हेरिया बॅसियाना",
        "metarhizium anisopliae": "मेटारिझियम अनिसोप्लिया",
        "verticillium lecanii": "व्हर्टिसिलियम लेकानी",
        "nuclear polyhedrosis virus": "एन.पी.व्ही विषाणू",
        "npv": "एन.पी.व्ही",
        # Botanicals
        "neem seed kernel extract": "निंबोळी अर्क",
        "nske": "निंबोळी अर्क",
        "neem oil": "कडुनिंब तेल",
        # Fungicides
        "copper oxychloride": "कॉपर ऑक्सिक्लोराईड",
        "streptocycline": "स्ट्रेप्टोसायक्लिन",
        "hexaconazole": "हेक्साकोनाझोल",
        "propiconazole": "प्रोपिकोनाझोल",
        "tricyclazole": "ट्रायसायक्लॅझोल",
        "carbendazim": "कार्बेन्डाझिम",
        "mancozeb": "मॅनकोझेब",
        "edifenphos": "एडीफेनफॉस",
        "thiram": "थायरम",
        "captan": "कॅप्टन",
        "metalaxyl": "मेटालॅक्सिल",
        "dinocap": "डिनोकॅप",
        "wettable sulphur": "पाण्यात मिसळणारा गंधक",
        "bordeaux mixture": "बोर्डो मिश्रण",
        "kasugamycin": "कासुगामायसिन",
        "validamycin": "व्हॅलिडामायसिन",
        "chlorothalonil": "क्लोरोथॅलोनिल",
        "zineb": "झिनेब",
        "carboxin": "कार्बोक्सिन",
        # Insecticides
        "chlorpyriphos": "क्लोरपायरीफॉस",
        "chlorpyrifos": "क्लोरपायरीफॉस",
        "imidacloprid": "इमिडाक्लोप्रिड",
        "dimethoate": "डायमेथोएट",
        "malathion": "मॅलाथिऑन",
        "monocrotophos": "मोनोक्रोटोफॉस",
        "acephate": "ॲसिटेफ",
        "cypermethrin": "सायपरमेथ्रिन",
        "lambda-cyhalothrin": "लॅम्बडा-सायहॅलोथ्रिन",
        "thiamethoxam": "थायामेथोक्साम",
        "fipronil": "फिप्रोनिल",
        "spinosad": "स्पिनोसॅड",
        "cartap hydrochloride": "कार्टॅप हायड्रोक्लोराइड",
        "quinalphos": "क्विनॉलफॉस",
        "phosphamidon": "फॉस्फामिडॉन",
        "profenofos": "प्रोफेनोफॉस",
        "profenophos": "प्रोफेनोफॉस",
        "novaluron": "नोव्हाल्युरॉन",
        "indoxacarb": "इंडोक्साकार्ब",
        "flubendiamide": "फ्लुबेंडायमाइड",
        "chlorantraniliprole": "क्लोरँट्रानिलीप्रोल",
        "emamectin benzoate": "इमामेक्टिन बेंझोएट",
        "phorate": "फोरेट",
        "carbofuran": "कार्बोफ्युरॉन",
        "dichlorvos": "डायक्लोर्व्हॉस",
        "endosulfan": "एंडोसल्फान",
        # Diseases
        "rice blast": "करपा रोग",
        "false smut": "काजळी रोग",
        "bacterial leaf blight": "जिवाणूजन्य पानांचा करपा",
        "sheath blight": "शीथ ब्लाइट",
        "stem rot": "खोड कुज",
        "downy mildew": "केवडा रोग",
        "powdery mildew": "भुरी रोग",
        "leaf spot": "पानावरील ठिपके",
        "tikka leaf spot": "टिक्का पानावरील ठिपके",
        "tikka disease": "टिक्का रोग",
        "wilt": "मर रोग",
        # Pests
        "brown planthopper": "तपकिरी तुडतुडे",
        "bph": "तपकिरी तुडतुडे",
        "yellow stem borer": "पिवळा खोडकिडा",
        "stem borer": "खोडकिडा",
        "gall midge": "गाद माशी",
        "leaf folder": "पान गुंडाळणारी अळी",
        "fall armyworm": "लष्करी अळी",
        "pink bollworm": "गुलाबी बोंडअळी",
        "bollworm": "बोंडअळी",
        "fruit borer": "फळ पोखरक",
        "whitefly": "पांढरी माशी",
        "aphids": "मावा",
        "thrips": "फुलकिडे",
        "mites": "लाल कोळी",
        "root-knot nematode": "सूत्रकृमी",
    },
    "hi": {
        # Institutions
        "krishi vigyan kendra": "कृषि विज्ञान केंद्र",
        "kvk": "केवीके",
        "icar": "आईसीएआर",
        "tnau": "टीएनएयू",
        # Biocontrol
        "trichoderma viride": "ट्राइकोडर्मा विरिडी",
        "trichoderma harzianum": "ट्राइकोडर्मा हार्ज़ियानम",
        "pseudomonas fluorescens": "स्यूडोमोनास फ्लोरेसेंस",
        "bacillus subtilis": "बैसिलस सबटिलिस",
        "beauveria bassiana": "ब्यूवेरिया बैसियाना",
        "metarhizium anisopliae": "मेटारिज़ियम एनीसोप्ली",
        "verticillium lecanii": "वर्टिसिलियम लेकानी",
        "nuclear polyhedrosis virus": "एनपीवी वायरस",
        "npv": "एनपीवी",
        # Botanicals
        "neem seed kernel extract": "नीम बीज गिरी सत्त",
        "nske": "नीम बीज गिरी सत्त",
        "neem oil": "नीम का तेल",
        # Fungicides
        "copper oxychloride": "कॉपर ऑक्सीक्लोराइड",
        "streptocycline": "स्ट्रेप्टोसाइक्लिन",
        "hexaconazole": "हेक्साकोनाजोल",
        "propiconazole": "प्रोपिकोनाजोल",
        "tricyclazole": "ट्राइसाइक्लाजोल",
        "carbendazim": "कार्बेंडाजिम",
        "mancozeb": "मैंकोजेब",
        "edifenphos": "एडीफेनफॉस",
        "thiram": "थीरम",
        "captan": "कैप्टन",
        "metalaxyl": "मेटालेक्सिल",
        "dinocap": "डिनोकैप",
        "wettable sulphur": "घुलनशील गंधक",
        "bordeaux mixture": "बोर्डो मिश्रण",
        "kasugamycin": "कासुगामाइसिन",
        "validamycin": "वैलिडामाइसिन",
        "chlorothalonil": "क्लोरोथैलोनिल",
        "zineb": "जिनेब",
        "carboxin": "कार्बोक्सिन",
        # Insecticides
        "chlorpyriphos": "क्लोरपायरीफॉस",
        "chlorpyrifos": "क्लोरपायरीफॉस",
        "imidacloprid": "इमिडाक्लोप्रिड",
        "dimethoate": "डाइमेथोएट",
        "malathion": "मैलाथियान",
        "monocrotophos": "मोनोक्रोटोफॉस",
        "acephate": "एसीफेट",
        "cypermethrin": "साइपरमेथ्रिन",
        "lambda-cyhalothrin": "लैम्ब्डा-साइहलोथ्रिन",
        "thiamethoxam": "थायमेथॉक्सम",
        "fipronil": "फिप्रोनिल",
        "spinosad": "स्पिनोसाड",
        "cartap hydrochloride": "कार्टाप हाइड्रोक्लोराइड",
        "quinalphos": "क्विनॉलफॉस",
        "phosphamidon": "फॉस्फामिडॉन",
        "profenofos": "प्रोफेनोफॉस",
        "profenophos": "प्रोफेनोफॉस",
        "novaluron": "नोवाल्यूरॉन",
        "indoxacarb": "इंडोक्साकार्ब",
        "flubendiamide": "फ्लूबेंडियामाइड",
        "chlorantraniliprole": "क्लोरेंट्रानिलीप्रोल",
        "emamectin benzoate": "इमामेक्टिन बेंजोएट",
        "phorate": "फोरेट",
        "carbofuran": "कार्बोफ्यूरॉन",
        "dichlorvos": "डाइक्लोरवॉस",
        "endosulfan": "एंडोसल्फान",
        # Diseases
        "rice blast": "झुलसा रोग",
        "false smut": "हल्दी रोग",
        "bacterial leaf blight": "जीवाणु पत्ती झुलसा",
        "sheath blight": "शीथ ब्लाइट",
        "stem rot": "तना गलन",
        "downy mildew": "मृदुरोमिल आसिता",
        "powdery mildew": "चूर्णिल आसिता",
        "leaf spot": "पत्ती धब्बा रोग",
        "tikka leaf spot": "टिक्का पत्ती धब्बा",
        "tikka disease": "टिक्का रोग",
        "wilt": "उकठा रोग",
        # Pests
        "brown planthopper": "भूरा फुदका",
        "bph": "भूरा फुदका",
        "yellow stem borer": "पीला तना छेदक",
        "stem borer": "तना छेदक",
        "gall midge": "गाल मिज",
        "leaf folder": "पत्ती लपेटक",
        "fall armyworm": "फॉल आर्मीवर्म",
        "pink bollworm": "गुलाबी सुंडी",
        "bollworm": "सुंडी",
        "fruit borer": "फल छेदक",
        "whitefly": "सफेद मक्खी",
        "aphids": "माहू",
        "thrips": "थ्रिप्स",
        "mites": "मकड़ी",
        "root-knot nematode": "सूत्रकृमि",
    },
    "te": {
        # Institutions
        "krishi vigyan kendra": "కృషి విజ్ఞాన కేంద్రం",
        "kvk": "కేవీకే",
        "icar": "ఐసీఏఆర్",
        "tnau": "టీఎన్‌ఏయూ",
        # Biocontrol
        "trichoderma viride": "ట్రైకోడెర్మా విరిడే",
        "trichoderma harzianum": "ట్రైకోడెర్మా హార్జియానమ్",
        "pseudomonas fluorescens": "సూడోమోనాస్ ఫ్లోరోసెన్స్",
        "bacillus subtilis": "బాసిల్లస్ సబ్టిలిస్",
        "beauveria bassiana": "బ్యూవేరియా బాసియానా",
        "metarhizium anisopliae": "మెటారైజియం అనిసోప్లియే",
        "verticillium lecanii": "వర్టిసిల్లియం లెకానీ",
        "nuclear polyhedrosis virus": "ఎన్‌పీవీ వైరస్",
        "npv": "ఎన్‌పీవీ",
        # Botanicals
        "neem seed kernel extract": "వేప గింజల కషాయం",
        "nske": "వేప గింజల కషాయం",
        "neem oil": "వేప నూనె",
        # Fungicides
        "copper oxychloride": "కాపర్ ఆక్సిక్లోరైడ్",
        "streptocycline": "స్ట్రెప్టోసైక్లిన్",
        "hexaconazole": "హెక్సాకోనాజోల్",
        "propiconazole": "ప్రొపికోనాజోల్",
        "tricyclazole": "ట్రైసైక్లాజోల్",
        "carbendazim": "కార్బెండజిమ్",
        "mancozeb": "మాంకోజెబ్",
        "edifenphos": "ఎడిఫెన్‌ఫాస్",
        "thiram": "థైరం",
        "captan": "కాప్టాన్",
        "metalaxyl": "మెటాలాక్సిల్",
        "dinocap": "దినోక్యాప్",
        "wettable sulphur": "నీటిలో కరిగే గంధకం",
        "bordeaux mixture": "బోర్డో మిశ్రమం",
        "kasugamycin": "కాసుగామైసిన్",
        "validamycin": "వాలిడామైసిన్",
        "chlorothalonil": "క్లోరోథలోనిల్",
        "zineb": "జినెబ్",
        "carboxin": "కార్బాక్సిన్",
        # Insecticides
        "chlorpyriphos": "క్లోర్‌పైరిఫాస్",
        "chlorpyrifos": "క్లోర్‌పైరిఫాస్",
        "imidacloprid": "ఇమిడాక్లోప్రిడ్",
        "dimethoate": "డైమెథోయేట్",
        "malathion": "మలాథియాన్",
        "monocrotophos": "మోనోక్రోటోఫాస్",
        "acephate": "ఎసిఫేట్",
        "cypermethrin": "సైపర్‌మెథ్రిన్",
        "lambda-cyhalothrin": "లాంబ్డా-సైహలోథ్రిన్",
        "thiamethoxam": "థయామెథోక్సామ్",
        "fipronil": "ఫిప్రోనిల్",
        "spinosad": "స్పినోసాడ్",
        "cartap hydrochloride": "కార్టాప్ హైడ్రోక్లోరైడ్",
        "quinalphos": "క్వినాల్ఫాస్",
        "phosphamidon": "ఫాస్ఫామిడాన్",
        "profenofos": "ప్రోఫెనోఫాస్",
        "profenophos": "ప్రొఫెనోఫాస్",
        "novaluron": "నోవాల్యురాన్",
        "indoxacarb": "ఇండోక్సాకార్బ్",
        "flubendiamide": "ఫ్లూబెండియమైడ్",
        "chlorantraniliprole": "క్లోరాంట్రానిలిప్రోల్",
        "emamectin benzoate": "ఎమామెక్టిన్ బెంజోయేట్",
        "phorate": "ఫోరేట్",
        "carbofuran": "కార్బోఫ్యూరాన్",
        "dichlorvos": "డైక్లోర్‌వాస్",
        "endosulfan": "ఎండోసల్ఫాన్",
        # Diseases
        "rice blast": "అగ్గి తెగులు",
        "false smut": "మసి తెగులు",
        "bacterial leaf blight": "బాక్టీరియా ఆకు ఎండు తెగులు",
        "sheath blight": "పాము పొడ తెగులు",
        "stem rot": "కాండం కుళ్ళు తెగులు",
        "downy mildew": "బూజు తెగులు",
        "powdery mildew": "బూడిద తెగులు",
        "leaf spot": "ఆకుమచ్చ తెగులు",
        "tikka leaf spot": "తిక్కా ఆకుమచ్చ తెగులు",
        "tikka disease": "తిక్కా తెగులు",
        "wilt": "ఎండు తెగులు",
        # Pests
        "brown planthopper": "సుడి దోమ",
        "bph": "సుడి దోమ",
        "yellow stem borer": "పసుపు కాండం తొలుచు పురుగు",
        "stem borer": "కాండం తొలుచు పురుగు",
        "gall midge": "ఉల్లికోడు",
        "leaf folder": "ఆకుచుట్టు పురుగు",
        "fall armyworm": "కత్తెర పురుగు",
        "pink bollworm": "గులాబీ రంగు కాయ తొలుచు పురుగు",
        "bollworm": "కాయ తొలుచు పురుగు",
        "fruit borer": "కాయ తొలుచు పురుగు",
        "whitefly": "తెల్లదోమ",
        "aphids": "పేనుబంక",
        "thrips": "తామర పురుగులు",
        "mites": "ఎర్ర నల్లి",
        "root-knot nematode": "వేరుబుడిపె నులిపురుగులు",
    }
}

# Pre-compile the regex pattern (sorted longest-first for greedy matching)
_sorted_terms = sorted(PROTECTED_TERMS, key=len, reverse=True)
_protect_re = re.compile(
    r'\b(' + '|'.join(re.escape(t) for t in _sorted_terms) + r')\b',
    re.IGNORECASE,
)


def format_bilingual(term: str, tgt: str) -> str:
    """Format protected term as: Native script (English) for farmer accessibility."""
    if tgt == "en":
        return term
    norm = term.lower().strip()
    dict_lang = BILINGUAL_GLOSSARY.get(tgt, {})
    if norm in dict_lang:
        regional = dict_lang[norm]
        if f"({term})" in regional or regional.endswith(f"({term})"):
            return regional
        return f"{regional} ({term})"
    return term


def _load(key):
    global DEVICE
    if key not in _cache:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        if DEVICE is None:
            DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        name = MODELS[key]
        tok = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(name, trust_remote_code=True).to(DEVICE).eval()
        _cache[key] = (tok, model)
    return _cache[key]


def translate_gemini(text: str, src: str, tgt: str) -> str:
    from google import genai
    from .config import GEMINI_API_KEY, GEMINI_MODEL
    client = genai.Client(api_key=GEMINI_API_KEY)
    lang_names = {"en": "English", "hi": "Hindi", "mr": "Marathi", "ta": "Tamil", "te": "Telugu"}
    src_name = lang_names.get(src, src)
    tgt_name = lang_names.get(tgt, tgt)
    prompt = (
        f"You are an agricultural translation engine for Indian smallholder farmers. "
        f"Translate the following text from {src_name} to {tgt_name}.\n"
        f"Requirements:\n"
        f"1. Keep all dosages, numbers, chemical formulations (e.g. 25 EC, 14.5 SC), and units (ml/L, kg/ha) strictly preserved.\n"
        f"2. Format chemical and pesticide names with bilingual clarity: Native script followed by English in parentheses where helpful.\n"
        f"3. Return ONLY the translated text, no preamble or extra chit-chat.\n\n"
        f"Text to translate:\n{text}"
    )
    resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return resp.text.strip()


def translate(text: str, src: str, tgt: str) -> str:
    if not text.strip() or src == tgt:
        return text
    from .config import GEMINI_API_KEY
    if GEMINI_API_KEY:
        try:
            return translate_gemini(text, src, tgt)
        except Exception as e:
            print(f"[TRANSLATE] Gemini translation error ({e}), falling back to IndicTrans2")
    import torch
    key = "indic-en" if tgt == "en" else "en-indic"
    tok, model = _load(key)
    ip = _get_ip()

    # --- Protect agronomic terms when translating EN -> Indic ---
    replacements = {}
    if src == "en" and tgt != "en":
        idx = 0
        def _repl(match):
            nonlocal idx
            tag = f"ZTAG{idx}Z"
            replacements[tag] = match.group(0)
            idx += 1
            return tag
        text = _protect_re.sub(_repl, text)

    sents = [s.strip() for s in re.split(r"(?<=[.!?।])\s+|\n+", text) if s.strip()]
    out = []
    for i in range(0, len(sents), 8):
        batch = ip.preprocess_batch(sents[i:i + 8], src_lang=CODES[src], tgt_lang=CODES[tgt])
        inputs = tok(batch, truncation=True, padding="longest", return_tensors="pt",
                     return_attention_mask=True).to(DEVICE)
        with torch.no_grad():
            gen = model.generate(**inputs, use_cache=True, min_length=0,
                                 max_length=256, num_beams=5, num_return_sequences=1)
        dec = tok.batch_decode(gen, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        out += ip.postprocess_batch(dec, lang=CODES[tgt])

    translated = " ".join(out)

    # --- Restore protected terms with bilingual formatting (Native + English) ---
    if replacements:
        for tag, orig in replacements.items():
            tag_num = tag[4:-1]  # from "ZTAG{idx}Z"
            bilingual_replacement = format_bilingual(orig, tgt)
            translated = re.sub(rf'(?:(?:ZTAG|झेडटीएजी|ज़ेडटीएजी)\s*{tag_num}\s*(?:Z|झेड|ज़ेड)|<{{1,2}}\s*{tag_num}\s*>{{1,2}})', bilingual_replacement, translated, flags=re.IGNORECASE)

    return translated
