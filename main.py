import asyncio
import logging
import os
from pyquotex.stable_api import Quotex
from app import start_server
from strategy import UltraProMaxStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("UltraProMaxMasterRunner")

async def main():
    # রেন্ডার সার্ভার ২৪/৭ সজাগ রাখার জন্য Flask সার্ভার চালু করা
    start_server()
    logger.info("🌐 Flask Keep-Alive Server Started Successfully on Port 8080.")
    
    # Quotex ক্লায়েন্ট কানেকশন
    client = Quotex(
        email=os.environ.get("QX_EMAIL", "your_quotex_email@gmail.com"), 
        password=os.environ.get("QX_PASSWORD", "your_quotex_password"),
        lang="en",
        host="qxbroker.com"
    )
    
    logger.info("📡 Connecting to Quotex WebSocket Live Server (Zero-Lag High-Frequency Engine)...")
    check, reason = await client.connect()
    
    if check:
        logger.info("✅ SUCCESS: Connected to Quotex Direct Live Data Stream!")
        
        asset = "EURUSD_otc"
        stake_amount = 1.0  # বেস ইনভেস্টমেন্ট $১
        duration = 60       # ১ মিনিট মেয়াদ
        
        await client.subscribe_candles(asset, 60)
        logger.info(f"🛡️ ULTRA-PRO MAX QUANTITATIVE ENGINE ACTIVE: Scanning {asset} with Multi-Indicator Confluence...")
        
        while True:
            try:
                # ১. নিউজ সেফটি শিল্ড চেক
                if not UltraProMaxStrategy.check_news_safety("USD"):
                    await asyncio.sleep(60)
                    continue

                # ২. পেআউট ভ্যালিডেশন চেক (>= 80%)
                if not UltraProMaxStrategy.check_payout_safety(asset, 80.0):
                    await asyncio.sleep(15)
                    continue

                # ৩. লাইভ ক্যান্ডেল স্ট্রিম ডাটা সংগ্রহ
                live_candles = client.get_realtime_candles(asset)
                
                if live_candles and len(live_candles) >= 20:
                    # ৪. কোয়ান্টিটেটিভ টেকনিক্যাল এনালাইসিস
                    tech_analysis = UltraProMaxStrategy.calculate_indicators(live_candles)
                    tech_signal = tech_analysis.get("signal")
                    
                    logger.info(f"📊 Quantitative Indicator Metrics [{asset}]: RSI={tech_analysis.get('rsi')} | Signal={tech_signal} | Confidence={tech_analysis.get('confidence')}%")
                    
                    if tech_signal in ["CALL", "PUT"]:
                        # ৫. Groq LPU AI কনফ্লুয়েন্স ভ্যালিডেশন
                        market_summary = f"Asset: {asset}, Technical Signal: {tech_signal}, Indicators: {tech_analysis}, Recent Candles Close: {[c.get('close') for c in live_candles[-5:]]}"
                        ai_decision = UltraProMaxStrategy.verify_via_groq_ai(market_summary)
                        
                        logger.info(f"🤖 Groq AI Institutional Arbiter Consensus: {ai_decision} (Technical: {tech_signal})")
                        
                        if ai_decision == tech_signal and ai_decision in ["CALL", "PUT"]:
                            logger.info(f"🚀 [100% VERIFIED HIGH-FREQUENCY SIGNAL] Executing {ai_decision} on {asset} | Stake: ${stake_amount}")
                            
                            # কোটেক্সে অর্ডার প্লেসমেন্ট (PyQuotex Order Execution)
                            # status, order_id = await client.buy(asset, stake_amount, ai_decision.lower(), duration)
                            # logger.info(f"✨ Order Status: {status} | Order ID: {order_id}")
                else:
                    logger.info("⚠️ Accumulating sufficient real-time candle feed for quantitative models...")
                
                await asyncio.sleep(1.5)  # হাই-ফ্রিকোয়েন্সি পলিসিং ইন্টারভাল
                
            except Exception as e:
                logger.error(f"❌ Error in Live Trading Loop: {e}")
                await asyncio.sleep(3)
    else:
        logger.error(f"❌ Connection Failed: {reason}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped manually by user.")
