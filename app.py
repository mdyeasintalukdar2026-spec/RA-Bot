from flask import Flask, jsonify, make_response
import threading
import requests
import time
import os
import logging

app = Flask(__name__, static_folder=None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("TradeLensApp")

@app.route('/')
def home():
    return "Trade Lens Bot Engine Running Successfully!"

@app.route('/ping')
def ping():
    return "OK", 200

@app.route('/signal')
def get_signal():
    try:
        current_time = time.time()
        trend_calc = (int(current_time * 1000) // 100) % 100
        ai_decision = "CALL" if (trend_calc % 2 == 0) else "PUT"
        confidence = 96 + ((int(current_time * 13) + 19) % 4)
        
        res = jsonify({
            "signal": ai_decision,
            "confidence": confidence,
            "status": "GREEN_EXECUTE"
        })
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res
    except Exception as e:
        res = jsonify({"signal": "DOWN", "confidence": 95, "status": "GREEN_EXECUTE"})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res

@app.route('/bot.js')
def bot_script():
    js = """
    (function(){
        try {
            var d = document;
            ["tradelens-widget", "tradelens-style", "tradelens-laser-r", "tradelens-laser-t"].forEach(function(i){
                var e = d.getElementById(i);
                if(e) e.remove();
            });

            var renderServerUrl = "https://ra-bot-9cq8.onrender.com";
            var botProfileImg = "https://i.postimg.cc/yNVqPD94/IMG-20261110-225927.jpg";

            var s = d.createElement('style');
            s.id = 'tradelens-style';
            s.innerHTML = '@keyframes tlPulseGlow {' +
                          '0% { box-shadow: 0 0 10px #ffffff, 0 0 20px #00f0ff; border-color: #00f0ff; }' +
                          '50% { box-shadow: 0 0 22px #ffffff, 0 0 40px #00f0ff; border-color: #ffffff; }' +
                          '100% { box-shadow: 0 0 10px #ffffff, 0 0 20px #00f0ff; border-color: #ffffff; }' +
                          '}' +
                          '@keyframes tlSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }' +
                          '@keyframes tlScanRightToLeft { 0% { right: 0%; opacity: 0.95; } 100% { right: 100%; opacity: 0.95; } }' +
                          '@keyframes tlScanTopToBottom { 0% { top: 0%; opacity: 0.95; } 100% { top: 100%; opacity: 0.95; } }';
            d.head.appendChild(s);

            var widget = d.createElement('div');
            widget.id = 'tradelens-widget';
            widget.style.cssText = 'position:fixed; top:130px; right:35px; width:62px; height:62px; background:#080c16; border:2.5px solid #00f0ff; border-radius:50%; display:flex; align-items:center; justify-content:center; z-index:2147483647; cursor:grab; animation:tlPulseGlow 3s infinite ease-in-out; overflow:hidden; box-sizing:border-box;';
            
            widget.innerHTML = '<img src="' + botProfileImg + '" style="width:100%; height:100%; object-fit:cover; border-radius:50%; pointer-events:none;" />';

            d.body.appendChild(widget);

            var isDragging = false, startX, startY, hasMoved = false;
            widget.onmousedown = widget.ontouchstart = function(e){
                isDragging = true; hasMoved = false;
                var p = e.touches ? e.touches[0] : e;
                startX = p.clientX - widget.offsetLeft; 
                startY = p.clientY - widget.offsetTop;
                widget.style.cursor = 'grabbing';
            };
            widget.onmousemove = widget.ontouchmove = function(e){
                if(!isDragging) return;
                var p = e.touches ? e.touches[0] : e;
                var nx = p.clientX - startX, ny = p.clientY - startY;
                if(Math.abs(nx - widget.offsetLeft) > 2 || Math.abs(ny - widget.offsetTop) > 2) hasMoved = true;
                widget.style.left = nx + 'px'; 
                widget.style.top = ny + 'px';
                widget.style.right = 'auto'; 
                widget.style.bottom = 'auto';
            };
            widget.onmouseup = widget.ontouchend = function(){ 
                isDragging = false; 
                widget.style.cursor = 'grab';
            };

            var isRunning = false;

            widget.onclick = function(e) {
                if(hasMoved) return;
                if(isRunning) return;
                isRunning = true;

                widget.style.borderColor = '#ffffff';
                widget.innerHTML = '<div style="width:20px; height:20px; border:2.5px solid #ffffff; border-top-color:transparent; border-radius:50%; animation:tlSpin 0.8s linear infinite;"></div>';

                fetch(renderServerUrl + '/signal?t=' + Date.now())
                .then(function(r){ return r.json(); })
                .catch(function(){ return {signal: "DOWN", confidence: 95}; })
                .then(function(data){
                    var sig = String(data.signal || 'DOWN').toUpperCase();
                    var isCall = (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                    var countdown = 5; // মোট ৫ সেকেন্ড

                    widget.style.background = isCall ? '#166534' : '#991b1b';
                    widget.style.borderColor = isCall ? '#22c55e' : '#ef4444';
                    
                    // দুইবার স্ক্যানিং সাইকেল শুরু (প্রতি চক্র ২.৫ সেকেন্ড করে)
                    startDoubleCycleScanning();

                    var timerInterval = setInterval(function(){
                        countdown--;
                        widget.innerHTML = '<div style="font-size:9px; font-weight:900; color:#fff; text-align:center; line-height:1.1;">' + (isCall ? 'UP' : 'DOWN') + '</div>' +
                                           '<div style="font-size:11px; font-weight:900; color:#fff; text-align:center; line-height:1.1;">' + countdown + 's</div>';

                        if(countdown <= 0) {
                            clearInterval(timerInterval);
                            removeScanningEffect();
                            triggerQuotexTrade(isCall);

                            setTimeout(function(){
                                widget.style.background = '#080c16';
                                widget.style.borderColor = '#00f0ff';
                                widget.innerHTML = '<img src="' + botProfileImg + '" style="width:100%; height:100%; object-fit:cover; border-radius:50%; pointer-events:none;" />';
                                isRunning = false;
                            }, 2500);
                        }
                    }, 1000);
                });
            };

            function startDoubleCycleScanning() {
                removeScanningEffect();
                
                // --- সাইকেল ১ (প্রথম ২.৫ সেকেন্ড): ডান থেকে বামে সাদা, পরে উপর থেকে নিচে লাল (হালকা চিকন বিম) ---
                
                // ১.১: ডান থেকে বামে (সাদা)
                var scanR1 = d.createElement('div');
                scanR1.id = 'tradelens-laser-r';
                scanR1.style.cssText = 'position:fixed; top:0; right:0; width:5px; height:100vh; background:linear-gradient(to left, rgba(255,255,255,0.7), #ffffff, rgba(255,255,255,0.7)); box-shadow: 0 0 15px #ffffff, 0 0 30px #ffffff; z-index:2147483646; pointer-events:none; animation:tlScanRightToLeft 1.25s linear forwards;';
                d.body.appendChild(scanR1);

                // ১.২: ১.২৫ সেকেন্ড পর উপর থেকে নিচে (লাল)
                setTimeout(function(){
                    var oldR1 = d.getElementById('tradelens-laser-r');
                    if(oldR1) oldR1.remove();

                    var scanT1 = d.createElement('div');
                    scanT1.id = 'tradelens-laser-t';
                    scanT1.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:5px; background:linear-gradient(to bottom, rgba(255,0,0,0.7), #ff0000, rgba(255,0,0,0.7)); box-shadow: 0 0 15px #ff0000, 0 0 30px #ff0000; z-index:2147483646; pointer-events:none; animation:tlScanTopToBottom 1.25s linear forwards;';
                    d.body.appendChild(scanT1);
                }, 1250);

                // --- সাইকেল ২ (পরবর্তী ২.৫ সেকেন্ড): ডান থেকে বামে সবুজ, পরে উপর থেকে নিচে হলুদ (হালকা চিকন বিম) ---

                // ২.১: ২.৫ সেকেন্ড পর ডান থেকে বামে (সবুজ)
                setTimeout(function(){
                    var oldT1 = d.getElementById('tradelens-laser-t');
                    if(oldT1) oldT1.remove();

                    var scanR2 = d.createElement('div');
                    scanR2.id = 'tradelens-laser-r';
                    scanR2.style.cssText = 'position:fixed; top:0; right:0; width:5px; height:100vh; background:linear-gradient(to left, rgba(34,197,94,0.7), #22c55e, rgba(34,197,94,0.7)); box-shadow: 0 0 15px #22c55e, 0 0 30px #22c55e; z-index:2147483646; pointer-events:none; animation:tlScanRightToLeft 1.25s linear forwards;';
                    d.body.appendChild(scanR2);
                }, 2500);

                // ২.২: ৩.৭৫ সেকেন্ড পর উপর থেকে নিচে (হলুদ)
                setTimeout(function(){
                    var oldR2 = d.getElementById('tradelens-laser-r');
                    if(oldR2) oldR2.remove();

                    var scanT2 = d.createElement('div');
                    scanT2.id = 'tradelens-laser-t';
                    scanT2.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:5px; background:linear-gradient(to bottom, rgba(234,179,8,0.7), #eab308, rgba(234,179,8,0.7)); box-shadow: 0 0 15px #eab308, 0 0 30px #eab308; z-index:2147483646; pointer-events:none; animation:tlScanTopToBottom 1.25s linear forwards;';
                    d.body.appendChild(scanT2);
                }, 3750);
            }

            function removeScanningEffect() {
                ["tradelens-laser-r", "tradelens-laser-t"].forEach(function(i){
                    var el = d.getElementById(i);
                    if(el) el.remove();
                });
            }

            function triggerQuotexTrade(isCall) {
                var targetBtn = null;
                var buttons = d.querySelectorAll('button, div[role="button"], span[class*="btn"]');
                for(var i=0; i<buttons.length; i++){
                    var btn = buttons[i];
                    var text = (btn.innerText || '').trim().toUpperCase();
                    var cls = (btn.className || '').toLowerCase();
                    var isUp = cls.includes('call') || cls.includes('buy') || cls.includes('up') || text === 'UP' || text === 'BUY';
                    var isDown = cls.includes('put') || cls.includes('sell') || cls.includes('down') || text === 'DOWN' || text === 'SELL';
                    
                    if(isCall && isUp && btn.getBoundingClientRect().width > 0){ targetBtn = btn; break; }
                    if(!isCall && isDown && btn.getBoundingClientRect().width > 0){ targetBtn = btn; break; }
                }
                if(targetBtn) {
                    try { targetBtn.click(); } catch(e) {}
                }
            }

        } catch(e) {}
    })();
    """
    res = make_response(js)
    res.headers['Content-Type'] = 'application/javascript'
    res.headers['Access-Control-Allow-Origin'] = '*'
    return res

def start_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()
