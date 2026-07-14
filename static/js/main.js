let chartInstance = null;
let currentThemeColor = '#3b82f6';
let actualLogs = [];

document.addEventListener('DOMContentLoaded', () => {
    // 1. Fetch Logs
    fetch('/api/logs')
        .then(res => res.json())
        .then(logs => {
            actualLogs = logs;
            // Build chart based on REAL data
            buildRealChart(actualLogs);
            buildHeatmap(actualLogs);
        })
        .catch(err => console.error("Error fetching logs:", err));

    // 2. Fetch Stats
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('accuracy').textContent = data.accuracy;
            document.getElementById('avg-rate').textContent = '0.0';
        });
        
    const video = document.getElementById('ai-video');
    const logList = document.getElementById('activity-log');
    let logIndex = 0;

    addLog('AI System Online. Menjalankan video, memindai area feedmill...', 0);

    video.addEventListener('timeupdate', () => {
        if (!actualLogs || actualLogs.length === 0) return;
        
        const sec = video.currentTime;
        let correctIndex = 0;
        
        // Update Heatmap Progress
        const duration = video.duration || 1;
        const pct = (sec / duration) * 100;
        document.getElementById('heatmap-progress').style.width = `${pct}%`;
        document.getElementById('heatmap-indicator').style.left = `${pct}%`;
        
        while (correctIndex < actualLogs.length && actualLogs[correctIndex].time <= sec) {
            correctIndex++;
        }
        
        // Update counters regardless of search
        updateDashboardCounters(correctIndex, sec);
        
        // If user is searching, do not auto-update the log DOM
        const searchInput = document.getElementById('log-search');
        if (searchInput && searchInput.value.trim() !== '') {
            return;
        }

        if (window._forceLogRefresh) {
            logIndex = -1; // Force full re-render
            logList.innerHTML = '';
            addLog('AI System Online. Menjalankan video, memindai area feedmill...', 0);
            window._forceLogRefresh = false;
        }
        
        if (correctIndex !== logIndex) {
            if (correctIndex > logIndex && logIndex !== -1) {
                const start = Math.max(logIndex, correctIndex - 5);
                for (let i = start; i < correctIndex; i++) {
                    const entry = actualLogs[i];
                    addLog('', entry.time, entry.id);
                }
            } else {
                logList.innerHTML = '';
                addLog('AI System Online. Menjalankan video, memindai area feedmill...', 0);
                const start = Math.max(0, correctIndex - 10);
                for (let i = start; i < correctIndex; i++) {
                    const entry = actualLogs[i];
                    addLog('', entry.time, entry.id);
                }
            }
            logIndex = correctIndex;
        }
    });
    
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
        
        // Group logic: we have a 12 min video, group by minute (0-11)
        let data = new Array(12).fill(0);
        logs.forEach(log => {
            let minuteIndex = Math.floor(log.time / 60);
            if(minuteIndex < 12) {
                data[minuteIndex]++;
            } else {
                data[11]++; // fallback for anything over 12 mins
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
        if(peakEl) peakEl.innerText = `Menit Tersibuk: Menit ke-${peakMinute} (${maxCount} karung)`;
        
        const gapEl = document.getElementById('avg-gap');
        if(gapEl) gapEl.innerText = `Rata-rata Jeda: ${avgGap} Detik/Karung`;
        
        const gradient = ctx.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.4)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mnt 1', 'Mnt 2', 'Mnt 3', 'Mnt 4', 'Mnt 5', 'Mnt 6', 'Mnt 7', 'Mnt 8', 'Mnt 9', 'Mnt 10', 'Mnt 11', 'Mnt 12'],
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
                        // Seek video to the beginning of that minute
                        const targetTime = idx * 60;
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

    // 1. Transfer absolute stats data to print template (instead of relying on current playback time)
    const totalCount = actualLogs ? actualLogs.length : 0;
    const finalWeight = ((totalCount * 50) / 1000).toFixed(2);
    const finalAvg = (totalCount / 12).toFixed(1); // Assuming 12 mins video

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
      filename:     'Laporan_Resmi_Analitik_Karung_27_Juni_2026.pdf',
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
    
    // Header Metadata
    csvContent += "LAPORAN DATA MENTAH (RAW DATA) DETEKSI KARUNG AI\n";
    csvContent += "Tanggal Sinkronisasi:,27 Juni 2026\n";
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
    link.setAttribute("download", "Data_Mentah_Karung_27_Juni_2026.csv");
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
