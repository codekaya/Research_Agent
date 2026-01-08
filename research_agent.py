#!/usr/bin/env python3
"""
Market & Trend Research Agent
=============================
Verilen bir anahtar kelime (niş) hakkında interneti tarayarak
trendler, sorunlar ve fırsatları analiz eden production-ready agent.

Author: AI Market Research Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict

from dotenv import load_dotenv
from tavily import TavilyClient
from google import genai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result from Tavily."""
    title: str
    url: str
    content: str
    score: float = 0.0


@dataclass
class ResearchData:
    """Holds all research data collected during the analysis."""
    topic: str
    timestamp: str
    trend_results: list[SearchResult] = field(default_factory=list)
    problem_results: list[SearchResult] = field(default_factory=list)
    question_results: list[SearchResult] = field(default_factory=list)
    analysis: str = ""
    raw_data: dict = field(default_factory=dict)


class ResearchAgent:
    """
    Market & Trend Research Agent
    
    Bu agent, verilen bir anahtar kelime hakkında internet araştırması yaparak
    trendleri, sorunları ve fırsatları analiz eder.
    """
    
    # System prompt for LLM analysis
    ANALYSIS_SYSTEM_PROMPT = """Sen bir ürün geliştirme danışmanısın ve pazar araştırması uzmanısın.

Sana verilen arama sonuçlarını dikkatlice analiz et ve şu başlıklar altında detaylı bir rapor hazırla:

## 📈 Yükselen Trendler
Bu alandaki güncel ve yükselen trendleri listele. Hangi teknolojiler, yaklaşımlar veya çözümler popülerlik kazanıyor?

## 😤 Kullanıcı Şikayetleri ve Acı Noktaları (Pain Points)
İnsanların bu konuyla ilgili en çok neyi zor bulduğunu, neden şikayet ettiğini ve hangi sorunlarla karşılaştığını belirt. 
Spesifik örnekler ve alıntılar varsa onları da ekle.

## 💡 Fırsat Alanları
Bu sorunlara çözüm olabilecek potansiyel ürün veya hizmet fırsatlarını belirle.
Hangi boşluklar doldurulabilir? Hangi ihtiyaçlar karşılanmamış?

## 🎯 Öneriler
Bir girişimci veya ürün geliştirici olarak bu bilgilerden nasıl yararlanılabilir? 
3-5 maddelik aksiyon önerileri sun.

Raporunu Türkçe olarak, profesyonel ve okunabilir bir formatta hazırla.
Maddeler halinde, emoji kullanarak ve net bir dille yaz."""

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ):
        """
        ResearchAgent'ı başlat.
        
        Args:
            tavily_api_key: Tavily API anahtarı (opsiyonel, env'den alınabilir)
            gemini_api_key: Gemini API anahtarı (opsiyonel, env'den alınabilir)
            model: Kullanılacak LLM modeli
        """
        # API anahtarlarını al
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        
        # API anahtarlarını doğrula
        self._validate_api_keys()
        
        # Client'ları başlat
        self.tavily_client = TavilyClient(api_key=self.tavily_api_key)
        self.gemini_client = genai.Client(api_key=self.gemini_api_key)
        
        logger.info("ResearchAgent başarıyla başlatıldı.")
    
    def _validate_api_keys(self) -> None:
        """API anahtarlarının varlığını doğrula."""
        missing_keys = []
        
        if not self.tavily_api_key:
            missing_keys.append("TAVILY_API_KEY")
        if not self.gemini_api_key:
            missing_keys.append("GEMINI_API_KEY")
        
        if missing_keys:
            raise ValueError(
                f"Eksik API anahtarları: {', '.join(missing_keys)}. "
                "Lütfen .env dosyasına ekleyin veya environment variable olarak tanımlayın."
            )
    
    def _generate_queries(self, topic: str) -> dict[str, str]:
        """
        Konu için akıllı arama sorguları oluştur.
        
        Args:
            topic: Araştırılacak konu
            
        Returns:
            Sorgu türü -> sorgu metni eşleştirmesi
        """
        current_year = datetime.now().year
        
        queries = {
            "trend": f"{topic} latest trends news {current_year}",
            "problem": f"site:reddit.com {topic} 'struggling with' OR 'hate' OR 'hard to' OR 'problem with'",
            "question": f"{topic} how to fix OR alternative to OR best solution for"
        }
        
        logger.info(f"'{topic}' için 3 farklı sorgu oluşturuldu.")
        return queries
    
    def _execute_search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """
        Tavily API kullanarak arama yap.
        
        Args:
            query: Arama sorgusu
            max_results: Maksimum sonuç sayısı
            
        Returns:
            Arama sonuçlarının listesi
        """
        try:
            logger.info(f"Tavily araması yapılıyor: '{query[:50]}...'")
            
            response = self.tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_raw_content=False
            )
            
            results = []
            for item in response.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0)
                ))
            
            logger.info(f"  → {len(results)} sonuç bulundu.")
            return results
            
        except Exception as e:
            logger.error(f"Tavily arama hatası: {e}")
            return []
    
    def _prepare_content_for_analysis(self, data: ResearchData) -> str:
        """
        LLM analizi için içerikleri hazırla.
        
        Args:
            data: Toplanan araştırma verileri
            
        Returns:
            Analiz için formatlanmış metin
        """
        sections = []
        
        # Trend sonuçları
        if data.trend_results:
            sections.append("=== TREND VE HABER SONUÇLARI ===")
            for i, result in enumerate(data.trend_results, 1):
                sections.append(f"\n[Trend {i}] {result.title}")
                sections.append(f"Kaynak: {result.url}")
                sections.append(f"İçerik: {result.content}\n")
        
        # Sorun/şikayet sonuçları (Reddit odaklı)
        if data.problem_results:
            sections.append("\n=== SORUN VE ŞİKAYET SONUÇLARI (Reddit/Forum) ===")
            for i, result in enumerate(data.problem_results, 1):
                sections.append(f"\n[Şikayet {i}] {result.title}")
                sections.append(f"Kaynak: {result.url}")
                sections.append(f"İçerik: {result.content}\n")
        
        # Soru sonuçları
        if data.question_results:
            sections.append("\n=== SORU VE ÇÖZÜM ARAMA SONUÇLARI ===")
            for i, result in enumerate(data.question_results, 1):
                sections.append(f"\n[Soru {i}] {result.title}")
                sections.append(f"Kaynak: {result.url}")
                sections.append(f"İçerik: {result.content}\n")
        
        return "\n".join(sections)
    
    def _analyze_with_llm(self, content: str, topic: str) -> str:
        """
        LLM kullanarak içerikleri analiz et.
        
        Args:
            content: Analiz edilecek ham içerik
            topic: Araştırılan konu
            
        Returns:
            LLM'in ürettiği analiz raporu
        """
        try:
            logger.info(f"LLM analizi başlatılıyor ({self.model})...")
            
            prompt = f"""{self.ANALYSIS_SYSTEM_PROMPT}

---

Araştırılan Konu: {topic}

Aşağıda bu konu hakkında toplanan arama sonuçları bulunmaktadır. 
Lütfen bunları analiz et ve yukarıdaki formatta bir rapor hazırla.

{content}"""
            
            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            
            analysis = response.text.strip()
            logger.info("LLM analizi tamamlandı.")
            return analysis
            
        except Exception as e:
            logger.error(f"LLM analiz hatası: {e}")
            return f"Analiz sırasında bir hata oluştu: {str(e)}"
    
    def _save_markdown_report(self, data: ResearchData, output_dir: str = ".") -> str:
        """
        Analiz sonuçlarını Markdown formatında kaydet.
        
        Args:
            data: Araştırma verileri
            output_dir: Çıktı dizini
            
        Returns:
            Oluşturulan dosyanın yolu
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rapor_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        report_content = f"""# 🔍 Pazar Araştırma Raporu

**Konu:** {data.topic}  
**Tarih:** {data.timestamp}  
**Oluşturan:** Market & Trend Research Agent

---

{data.analysis}

---

## 📊 Araştırma İstatistikleri

| Kategori | Sonuç Sayısı |
|----------|--------------|
| Trend Sonuçları | {len(data.trend_results)} |
| Sorun/Şikayet Sonuçları | {len(data.problem_results)} |
| Soru/Çözüm Sonuçları | {len(data.question_results)} |
| **Toplam** | **{len(data.trend_results) + len(data.problem_results) + len(data.question_results)}** |

---

## 🔗 Kaynak URL'leri

### Trend Kaynakları
{self._format_url_list(data.trend_results)}

### Sorun/Şikayet Kaynakları
{self._format_url_list(data.problem_results)}

### Soru/Çözüm Kaynakları
{self._format_url_list(data.question_results)}

---

*Bu rapor, Market & Trend Research Agent tarafından otomatik olarak oluşturulmuştur.*
"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        logger.info(f"Markdown raporu kaydedildi: {filepath}")
        return filepath
    
    def _format_url_list(self, results: list[SearchResult]) -> str:
        """URL listesini Markdown formatında biçimlendir."""
        if not results:
            return "- Sonuç bulunamadı"
        
        lines = []
        for result in results:
            lines.append(f"- [{result.title}]({result.url})")
        return "\n".join(lines)
    
    def _save_json_data(self, data: ResearchData, output_dir: str = ".") -> str:
        """
        Araştırma verilerini JSON formatında kaydet.
        
        Args:
            data: Araştırma verileri
            output_dir: Çıktı dizini
            
        Returns:
            Oluşturulan dosyanın yolu
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # SearchResult'ları dict'e çevir
        json_data = {
            "topic": data.topic,
            "timestamp": data.timestamp,
            "trend_results": [asdict(r) for r in data.trend_results],
            "problem_results": [asdict(r) for r in data.problem_results],
            "question_results": [asdict(r) for r in data.question_results],
            "analysis": data.analysis,
            "metadata": {
                "model_used": self.model,
                "total_results": (
                    len(data.trend_results) + 
                    len(data.problem_results) + 
                    len(data.question_results)
                )
            }
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON verisi kaydedildi: {filepath}")
        return filepath
    
    def _print_report(self, data: ResearchData) -> None:
        """Raporu konsola şık bir şekilde yazdır."""
        border = "=" * 60
        
        print(f"\n{border}")
        print("🔍 PAZAR ARAŞTIRMA RAPORU")
        print(border)
        print(f"📌 Konu: {data.topic}")
        print(f"📅 Tarih: {data.timestamp}")
        print(border)
        print()
        print(data.analysis)
        print()
        print(border)
        print(f"📊 Toplam {len(data.trend_results) + len(data.problem_results) + len(data.question_results)} kaynak analiz edildi.")
        print(border)
    
    def research(
        self,
        topic: str,
        output_dir: str = ".",
        max_results_per_query: int = 10,
        save_files: bool = True
    ) -> ResearchData:
        """
        Belirtilen konu hakkında kapsamlı araştırma yap.
        
        Args:
            topic: Araştırılacak konu/niş
            output_dir: Çıktı dosyalarının kaydedileceği dizin
            max_results_per_query: Her sorgu için maksimum sonuç sayısı
            save_files: Dosyaları kaydet (True) veya sadece konsola yazdır (False)
            
        Returns:
            Tüm araştırma verilerini içeren ResearchData objesi
        """
        logger.info(f"Araştırma başlatılıyor: '{topic}'")
        print(f"\n🚀 '{topic}' konusu için araştırma başlatılıyor...\n")
        
        # ResearchData oluştur
        data = ResearchData(
            topic=topic,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Sorguları oluştur
        queries = self._generate_queries(topic)
        
        # Aramaları yap
        print("📡 Veri toplama aşaması...")
        data.trend_results = self._execute_search(
            queries["trend"], 
            max_results_per_query
        )
        data.problem_results = self._execute_search(
            queries["problem"], 
            max_results_per_query
        )
        data.question_results = self._execute_search(
            queries["question"], 
            max_results_per_query
        )
        
        # İçerikleri hazırla
        content = self._prepare_content_for_analysis(data)
        
        if not content.strip():
            logger.warning("Analiz için yeterli içerik bulunamadı.")
            data.analysis = "Üzgünüz, bu konu hakkında yeterli veri bulunamadı."
        else:
            # LLM analizi
            print("🧠 Yapay zeka analizi yapılıyor...")
            data.analysis = self._analyze_with_llm(content, topic)
        
        # Raporu yazdır
        self._print_report(data)
        
        # Dosyaları kaydet
        if save_files:
            print("\n💾 Dosyalar kaydediliyor...")
            md_path = self._save_markdown_report(data, output_dir)
            json_path = self._save_json_data(data, output_dir)
            print(f"✅ Markdown raporu: {md_path}")
            print(f"✅ JSON verisi: {json_path}")
        
        print("\n✨ Araştırma tamamlandı!\n")
        return data


def main():
    """Ana giriş noktası."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           🔍 Market & Trend Research Agent v1.0              ║
║                                                              ║
║   Pazar trendleri, kullanıcı sorunları ve fırsatları        ║
║   keşfetmek için yapay zeka destekli araştırma aracı        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Kullanıcıdan konu al
    topic = input("🎯 Araştırılacak konuyu/nişi girin: ").strip()
    
    if not topic:
        print("❌ Hata: Lütfen geçerli bir konu girin.")
        sys.exit(1)
    
    try:
        # Agent'ı başlat ve araştırmayı çalıştır
        agent = ResearchAgent()
        agent.research(topic)
        
    except ValueError as e:
        print(f"\n❌ Konfigürasyon Hatası: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Araştırma kullanıcı tarafından iptal edildi.")
        sys.exit(0)
    except Exception as e:
        logger.exception("Beklenmeyen hata oluştu")
        print(f"\n❌ Beklenmeyen Hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
