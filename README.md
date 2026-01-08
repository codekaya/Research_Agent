# 🔍 Market & Trend Research Agent

Pazar trendleri, kullanıcı sorunları ve fırsatları keşfetmek için yapay zeka destekli araştırma aracı.

## 📋 Özellikler

- **Akıllı Sorgu Oluşturma**: Tek bir konudan 3 farklı açıdan arama yapılır
  - Trend sorguları (güncel haberler ve trendler)
  - Sorun sorguları (Reddit/forum odaklı şikayetler)
  - Soru sorguları (çözüm arayışları)
- **Gelişmiş Arama**: Tavily API ile derinlemesine web araması
- **AI Analizi**: Google Gemini ile kapsamlı içerik analizi
- **Çoklu Çıktı**: Markdown raporu + JSON veri dosyası
- **Production Ready**: Hata yönetimi, logging ve modüler yapı

## 🚀 Kurulum

### 1. Gereksinimleri Yükleyin

```bash
cd research_agent
pip install -r requirements.txt
```

### 2. API Anahtarlarını Ayarlayın

`.env.example` dosyasını `.env` olarak kopyalayın ve API anahtarlarınızı ekleyin:

```bash
cp .env.example .env
```

Ardından `.env` dosyasını düzenleyin:

```env
TAVILY_API_KEY=your_tavily_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**API Anahtarları Nereden Alınır?**
- [Tavily API](https://tavily.com/) - Ücretsiz tier mevcut
- [Google Gemini API](https://aistudio.google.com/app/apikey) - Ücretsiz tier mevcut

## 💻 Kullanım

### Komut Satırından

```bash
python research_agent.py
```

Script sizden araştırılacak konuyu isteyecektir:

```
🎯 Araştırılacak konuyu/nişi girin: Indie Game Marketing
```

### Kod İçinde Import Ederek

```python
from research_agent import ResearchAgent

# Agent'ı başlat
agent = ResearchAgent()

# Araştırma yap
result = agent.research(
    topic="No-code Tools",
    output_dir="./reports",
    max_results_per_query=15,
    save_files=True
)

# Sonuçlara eriş
print(result.analysis)
print(f"Toplam {len(result.trend_results)} trend bulundu")
```

### Özel Model Kullanma

```python
# Farklı bir model kullan
agent = ResearchAgent(model="gemini-2.0-flash")

# Veya API anahtarlarını doğrudan ver
agent = ResearchAgent(
    tavily_api_key="tvly-xxx",
    gemini_api_key="AIza...",
    model="gemini-2.5-flash"
)
```

## 📁 Çıktı Dosyaları

Script çalıştırıldığında iki dosya oluşturulur:

### `rapor_[tarih].md`
Okunabilir Markdown formatında detaylı rapor:
- Yükselen trendler
- Kullanıcı şikayetleri ve acı noktaları
- Fırsat alanları
- Aksiyon önerileri
- Kaynak URL'leri

### `data_[tarih].json`
Ham veri ve analiz sonuçlarını içeren JSON dosyası:
- Tüm arama sonuçları
- LLM analizi
- Metadata

## 🏗️ Proje Yapısı

```
research_agent/
├── research_agent.py   # Ana script
├── requirements.txt    # Python bağımlılıkları
├── .env.example        # Örnek environment dosyası
├── .env                # Gerçek API anahtarları (gitignore'da)
└── README.md           # Bu dosya
```

## ⚙️ Konfigürasyon

### Environment Variables

| Değişken | Açıklama | Zorunlu |
|----------|----------|---------|
| `TAVILY_API_KEY` | Tavily API anahtarı | ✅ |
| `GEMINI_API_KEY` | Google Gemini API anahtarı | ✅ |

### ResearchAgent Parametreleri

| Parametre | Varsayılan | Açıklama |
|-----------|------------|---------|
| `tavily_api_key` | env'den | Tavily API anahtarı |
| `gemini_api_key` | env'den | Gemini API anahtarı |
| `model` | `gemini-2.5-flash` | Kullanılacak LLM modeli |

### research() Parametreleri

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| `topic` | - | Araştırılacak konu (zorunlu) |
| `output_dir` | `.` | Çıktı dizini |
| `max_results_per_query` | `10` | Sorgu başına maks sonuç |
| `save_files` | `True` | Dosyaları kaydet |

## 🔒 Güvenlik

- API anahtarlarını asla commit etmeyin
- `.env` dosyasını `.gitignore`'a ekleyin
- Production'da environment variables kullanın

## 📝 Lisans

MIT License
