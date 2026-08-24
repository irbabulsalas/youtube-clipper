const API_BASE = '/api';
let token = localStorage.getItem('token');

(async () => {
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/me`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!res.ok) {
            window.location.href = '/login.html';
            return;
        }
        
        const user = await res.json();
        document.getElementById('userInfo').textContent = user.username + (user.is_admin ? ' (admin)' : '');
    } catch (e) {
        window.location.href = '/login.html';
    }
})();

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('is_admin');
    window.location.href = '/login.html';
}

async function authFetch(url, options = {}) {
    const res = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': 'Bearer ' + token
        }
    });
    
    if (res.status === 401) {
        window.location.href = '/login.html';
        throw new Error('Session expired');
    }
    
    return res;
}

document.getElementById('clipForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        youtube_url: document.getElementById('youtubeUrl').value,
        aspect_ratio: document.getElementById('aspectRatio').value,
        subtitle_language: document.getElementById('subtitleLanguage').value,
        max_clips: parseInt(document.getElementById('maxClips').value),
        min_clip_duration: parseInt(document.getElementById('minDuration').value),
        max_clip_duration: 180
    };
    
    document.getElementById('progress').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    document.getElementById('submitBtn').disabled = true;
    
    try {
        const response = await authFetch(`${API_BASE}/clip/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Gagal memulai job');
        }
        
        const job = await response.json();
        pollStatus(job.job_id);
        
    } catch (error) {
        showError(error.message);
    }
});

async function pollStatus(jobId) {
    try {
        const response = await authFetch(`${API_BASE}/clip/status/${jobId}`);
        
        if (!response.ok) {
            throw new Error('Gagal mengecek status');
        }
        
        const status = await response.json();
        
        document.getElementById('progressBar').style.width = `${status.progress}%`;
        document.getElementById('progressText').textContent = status.message;
        
        if (status.status === 'completed') {
            showResults(status.clips);
        } else if (status.status === 'error') {
            showError(status.error);
        } else {
            setTimeout(() => pollStatus(jobId), 2000);
        }
        
    } catch (error) {
        showError(error.message);
    }
}

function showResults(clips) {
    document.getElementById('progress').classList.add('hidden');
    document.getElementById('results').classList.remove('hidden');
    document.getElementById('submitBtn').disabled = false;
    
    const list = document.getElementById('clipsList');
    list.innerHTML = '';
    
    clips.forEach(clip => {
        const card = document.createElement('div');
        card.className = 'bg-gray-800 rounded-lg p-4';
        card.innerHTML = `
            <div class="flex justify-between items-center mb-2">
                <span class="text-sm text-gray-400">${formatTime(clip.start_time)} - ${formatTime(clip.end_time)}</span>
                <span class="text-xs bg-blue-600 px-2 py-1 rounded">${clip.aspect_ratio}</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-sm">Duration: ${Math.round(clip.duration)}s</span>
                <a 
                    href="${API_BASE}${clip.download_url}" 
                    class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg text-sm font-semibold transition"
                    download
                    onclick="setTimeout(() => location.reload(), 500)"
                >
                    Download
                </a>
            </div>
        `;
        list.appendChild(card);
    });
}

function showError(message) {
    document.getElementById('progress').classList.add('hidden');
    document.getElementById('error').classList.remove('hidden');
    document.getElementById('errorText').textContent = message;
    document.getElementById('submitBtn').disabled = false;
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}