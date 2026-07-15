let chartInstance = null;
let currentThemeColor = '#3b82f6';
let actualLogs = [];
let streamStartTime = Date.now();

document.addEventListener('DOMContentLoaded', () => {
    const img = document.getElementById('ai-video');
    const canvas = document.getElementById('ai-canvas');
    let ctx = null;
    if (canvas) {
        ctx = canvas.getContext('2d');
    }
    
    function resizeCanvas() {
        if (!canvas || !img) return;
        canvas.width = img.clientWidth;
        canvas.height = img.clientHeight;
    }
    
    // Original Video Resolution from OpenCV Cap (Fallback)
    let videoOriginalWidth = 1280;
    let videoOriginalHeight = 720;
    
    window.addEventListener('resize', resizeCanvas);
    if(img) {
        img.addEventListener('load', resizeCanvas);
        setTimeout(resizeCanvas, 500);
    }

    const logList = document.getElementById('activity-log');
    let logIndex = 0;
    let loggedIds = new Set();
    
    if (logList) addLog('AI System Online. Menjalankan Live Stream, memindai area feedmill...', 0);

    const evtSource = new EventSource('/api/stream_data');
    evtSource.onmessage = function(event) {
        if (!event.data) return;
        const data = JSON.parse(event.data);
        if (!data || Object.keys(data).length === 0) return;
        
        let currentSeconds = (Date.now() - streamStartTime) / 1000;
        updateDashboardCounters(data.total_count, currentSeconds); 
        
        if (!ctx) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (data.frame_width) videoOriginalWidth = data.frame_width;
        if (data.frame_height) videoOriginalHeight = data.frame_height;
        
        const scaleX = canvas.width / videoOriginalWidth;
        const scaleY = canvas.height / videoOriginalHeight;
        
        if (data.zone && data.zone.length > 0) {
            ctx.beginPath();
            ctx.moveTo(data.zone[0][0] * scaleX, data.zone[0][1] * scaleY);
            for(let i=1; i<data.zone.length; i++) {
                ctx.lineTo(data.zone[i][0] * scaleX, data.zone[i][1] * scaleY);
            }
            ctx.closePath();
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#00ff00';
            ctx.stroke();
            ctx.fillStyle = 'rgba(0, 255, 255, 0.2)';
            ctx.fill();
        }
        
        if (data.boxes) {
            data.boxes.forEach(box => {
                const x1 = box.bbox[0] * scaleX;
                const y1 = box.bbox[1] * scaleY;
                const w = (box.bbox[2] - box.bbox[0]) * scaleX;
                const h = (box.bbox[3] - box.bbox[1]) * scaleY;
                
                ctx.strokeStyle = '#00ff00';
                ctx.lineWidth = 2;
                ctx.strokeRect(x1, y1, w, h);
                
                ctx.font = 'bold 14px monospace';
                ctx.fillStyle = '#00ff00';
                ctx.fillText(`ID: ${box.id}`, x1, y1 - 5);
                
                if (box.badge) {
                    ctx.font = 'bold 24px monospace';
                    ctx.fillStyle = '#ff0000';
                    ctx.fillText('+1', x1 + (w/2) - 15, y1 + (h/2));
                    
                    if (!loggedIds.has(box.id)) {
                        let timeInSec = (Date.now() - streamStartTime) / 1000;
                        addLog('', timeInSec, box.id);
                        loggedIds.add(box.id);
                        
                        actualLogs.push({ time: timeInSec, id: box.id });
                        buildRealChart(actualLogs);
                        buildHeatmap(actualLogs);
                    }
                }
            });
        }
    };
    
    function updateDashboardCounters(currentSackCount, currentSeconds) {
        const totalSacksEl = document.getElementById('total-sacks');
        
        if (totalSacksEl.innerText != currentSackCount) {
            totalSacksEl.innerHTML = currentSackCount;
            totalSacksEl.classList.add('pop-animation');
            setTimeout(() => totalSacksEl.classList.remove('pop-animation'), 400);
        }
        
        const weightTon = (currentSackCount * 50) / 1000;
        document.getElementById('total-weight').innerHTML = weightTon.toFixed(2);
        
        if (currentSeconds > 0) {
            const mins = currentSeconds / 60;
            const avg = (currentSackCount / mins).toFixed(1);
            document.getElementById('avg-rate').textContent = avg;
        } else {
            document.getElementById('avg-rate').textContent = '0.0';
        }
    }
    
    function addLog(message, timeInSec, id=null) {
        const m = Math.floor(timeInSec / 60).toString().padStart(2, '0');
        const s = Math.floor(timeInSec % 60).toString().padStart(2, '0');
        const item = document.createElement('div');
        item.className = 'log-item';
        
        item.style.cursor = 'pointer';
        item.onclick = function() {
            document.getElementById('ai-video').currentTime = Math.max(0, timeInSec - 2);
            document.getElementById('ai-video').play();
        };

        let content = `<span class="log-time">[${m}:${s}]</span> `;
        if (id) {
            item.setAttribute('data-id', id);
            content += `Karung ID #${id} terdeteksi <span class="log-highlight">+1</span> di sabuk berjalan. Kapasitas truk bertambah.`;
        } else {
            content += message;
        }
        
        item.innerHTML = content;
        logList.prepend(item);
    }
    
    // Expose addLog globally for search to use
    window.addLogItemToDOM = addLog;
    
    function buildHeatmap(logs) {
        const heatmap = document.getElementById('video-heatmap');
        if (!heatmap) return;
        
        const vid = document.getElementById('ai-video');
        
        // Wait for metadata to know exact video duration for accurate mapping
        vid.addEventListener('loadedmetadata', () => {
            const duration = vid.duration;
            
            // Format duration string
            const m = Math.floor(duration / 60).toString().padStart(2, '0');
            const s = Math.floor(duration % 60).toString().padStart(2, '0');
            document.getElementById('video-duration').innerText = `${m}:${s}`;
            
            // Generate ticks for every log
            logs.forEach(log => {
                const pct = (log.time / duration) * 100;
                const tick = document.createElement('div');
                tick.style.position = 'absolute';
                tick.style.left = `${pct}%`;
                tick.style.top = '0';
                tick.style.width = '2px';
                tick.style.height = '100%';
                tick.style.background = 'rgba(16, 185, 129, 0.7)'; // Green line
                tick.style.boxShadow = '0 0 3px rgba(16, 185, 129, 0.5)';
                heatmap.appendChild(tick);
            });
            
            // Make heatmap clickable
            heatmap.addEventListener('click', (e) => {
                const rect = heatmap.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const clickPct = clickX / rect.width;
                vid.currentTime = clickPct * duration;
                vid.play();
            });
        });
        
        // Fallback if metadata is already loaded (sometimes happens when cached)
        if (vid.readyState >= 1) {
            vid.dispatchEvent(new Event('loadedmetadata'));
        }
    }
    
    function buildRealChart(logs) {
        const ctx = document.getElementById('distributionChart').getContext('2d');
        
        // Group logic: we have an 8-hour shift, group by hour (0-7)
        let data = new Array(8).fill(0);
        logs.forEach(log => {
            let hourIndex = Math.floor(log.time / 3600); // 3600 seconds = 1 hour
            if(hourIndex < 8) {
                data[hourIndex]++;
            } else {
                data[7]++; // fallback for anything over 8 hours
            }
        });
        
        // Smart Insights Calculations (No fake data!)
        let maxCount = 0;
        let peakMinute = 0;
        data.forEach((val, idx) => {
            if (val > maxCount) { maxCount = val; peakMinute = idx + 1; }
        });
        
        let totalGap = 0;
        let validGaps = 0;
        for (let i = 1; i < logs.length; i++) {
            totalGap += (logs[i].time - logs[i-1].time);
            validGaps++;
        }
        let avgGap = validGaps > 0 ? (totalGap / validGaps).toFixed(1) : "0.0";
        
        const peakEl = document.getElementById('peak-minute');
        if(peakEl) peakEl.innerText = `Jam Tersibuk: Jam ke-${peakMinute} (${maxCount} karung)`;
        
        const gapEl = document.getElementById('avg-gap');
        if(gapEl) gapEl.innerText = `Rata-rata Jeda: ${avgGap} Detik/Karung`;
        
        const gradient = ctx.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.4)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');
        
        if (chartInstance) {
            chartInstance.destroy();
        }

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jam ke-1', 'Jam ke-2', 'Jam ke-3', 'Jam ke-4', 'Jam ke-5', 'Jam ke-6', 'Jam ke-7', 'Jam ke-8'],
                datasets: [{
                    label: 'Karung Masuk',
                    data: data,
                    borderColor: currentThemeColor,
                    backgroundColor: gradient,
                    borderWidth: 3,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: currentThemeColor,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onClick: (e, activeEls) => {
                    if (activeEls.length > 0) {
                        const idx = activeEls[0].index;
                        // Seek video to the beginning of that hour
                        const targetTime = idx * 3600;
                        video.currentTime = targetTime;
                        video.play();
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#94a3b8',
                        padding: 10,
                        callbacks: {
                            label: function(context) { return context.raw + ' Karung Terdeteksi'; }
                        }
                    }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });
    }
});

// PDF Generation exposed to global scope
window.generatePDF = function() {
    const btn = document.getElementById('export-pdf');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="ph-bold ph-spinner" style="animation: spin 1s linear infinite;"></i> Memproses...';
    btn.disabled = true;
    
    // Format tanggal Indonesia
    const months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
    const d = new Date();
    const todayStr = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;

    // 1. Transfer absolute stats data to print template directly from UI
    const totalCount = document.getElementById('total-sacks').innerText || '0';
    const finalWeight = document.getElementById('total-weight').innerText || '0';
    const finalAvg = document.getElementById('avg-rate').innerText || '0.0';

    document.getElementById('print-total').innerText = totalCount;
    document.getElementById('print-weight').innerText = finalWeight + " Ton";
    // Accuracy is static, can grab from UI
    document.getElementById('print-acc').innerText = document.getElementById('accuracy').innerText || '98%';
    document.getElementById('print-rate').innerText = finalAvg + " Karung/Menit";

    // 2. Capture chart as image
    const chartCanvas = document.getElementById('distributionChart');
    if(chartCanvas) {
        document.getElementById('print-chart-img').src = chartCanvas.toDataURL('image/png');
    }

    const element = document.getElementById('print-template');
    
    // Pause video
    const vid = document.getElementById('ai-video');
    if(vid) vid.pause();

    // 3. Temporarily make the hidden template block display logic work for html2pdf
    element.parentElement.style.display = 'block';

    const opt = {
      margin:       0.5,
      filename:     `Laporan_Resmi_Analitik_Karung_${todayStr.replace(/ /g, '_')}.pdf`,
      image:        { type: 'jpeg', quality: 1.0 },
      html2canvas:  { scale: 2, useCORS: true },
      jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save().then(() => {
        element.parentElement.style.display = 'none'; // Hide again
        btn.innerHTML = '<i class="ph-bold ph-check"></i> Berhasil Disimpan!';
        btn.style.background = '#10b981';
        btn.style.boxShadow = '0 4px 15px rgba(16, 185, 129, 0.4)';
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.style.background = '';
            btn.style.boxShadow = '';
            btn.disabled = false;
        }, 2000);
    }).catch(err => {
        console.error(err);
        element.parentElement.style.display = 'none';
        btn.innerHTML = originalText;
        btn.disabled = false;
        alert("Gagal melakukan ekspor PDF.");
    });
};

// Global CSV Generation
window.generateCSV = function() {
    if (!actualLogs || actualLogs.length === 0) {
        alert("Data log belum tersedia.");
        return;
    }
    
    let csvContent = "data:text/csv;charset=utf-8,";
    
    const months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
    const d = new Date();
    const todayStr = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
    
    // Header Metadata
    csvContent += "LAPORAN DATA MENTAH (RAW DATA) DETEKSI KARUNG AI\n";
    csvContent += `Tanggal Sinkronisasi:,${todayStr}\n`;
    csvContent += "Lokasi Kamera:,Area Loading Dock A\n";
    csvContent += `Total Karung Terdeteksi:,${actualLogs.length} Karung\n`;
    csvContent += `Estimasi Total Berat:,${((actualLogs.length * 50) / 1000).toFixed(2)} Ton\n`;
    csvContent += "\n"; // Blank line separator
    
    // Table Headers
    csvContent += "ID Karung (Urutan),Waktu Deteksi (Detik),Format Waktu (Menit:Detik),Status Validasi\n";
    
    actualLogs.forEach(function(log) {
        const m = Math.floor(log.time / 60).toString().padStart(2, '0');
        const s = Math.floor(log.time % 60).toString().padStart(2, '0');
        csvContent += `${log.id},${log.time.toFixed(2)},${m}:${s},Valid (+1)\n`;
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Data_Mentah_Karung_${todayStr.replace(/ /g, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

// Global Log Filter (Search through entire video data)
window.filterLogs = function() {
    const input = document.getElementById('log-search').value.toLowerCase().trim();
    const logList = document.getElementById('activity-log');
    
    if (input === '') {
        // Restore synced playback view
        window._forceLogRefresh = true;
        return;
    }
    
    // Clear list to show search results
    logList.innerHTML = '';
    
    let foundCount = 0;
    actualLogs.forEach(entry => {
        const idStr = entry.id.toString();
        if (idStr.includes(input)) {
            window.addLogItemToDOM('', entry.time, entry.id);
            foundCount++;
        }
    });
    
    if (foundCount === 0) {
        logList.innerHTML = `<div style="padding: 15px; text-align: center; color: var(--text-secondary); font-size: 13px;">Karung dengan ID "${input}" tidak ditemukan dalam rekaman ini.</div>`;
    }
};
