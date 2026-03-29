// Grafana to Kibana Converter - Frontend JavaScript

class DashboardConverter {
    constructor() {
        this.selectedFile = null;
        this.currentFileId = null;
        this.currentJobId = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.checkApiStatus();
    }

    setupEventListeners() {
        // File input
        const fileInput = document.getElementById('file-input');
        const browseBtn = document.getElementById('browse-btn');
        const convertBtn = document.getElementById('convert-btn');

        browseBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));
        convertBtn.addEventListener('click', () => this.convertDashboard());

        // Action buttons
        document.getElementById('download-btn').addEventListener('click', () => {
            console.log('Download .json button clicked');
            this.downloadDashboard('json');
        });
        document.getElementById('download-ndjson-btn').addEventListener('click', () => {
            console.log('Download .ndjson button clicked');
            this.downloadDashboard('ndjson');
        });
        document.getElementById('preview-btn').addEventListener('click', () => this.previewConversion());
        document.getElementById('new-conversion-btn').addEventListener('click', () => this.resetForm());
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('upload-area');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => this.highlight(uploadArea), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => this.unhighlight(uploadArea), false);
        });

        uploadArea.addEventListener('drop', (e) => this.handleDrop(e), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlight(elem) {
        elem.classList.add('dragover');
    }

    unhighlight(elem) {
        elem.classList.remove('dragover');
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFileSelect(files[0]);
    }

    handleFileSelect(file) {
        if (!file) return;

        if (!file.name.endsWith('.json')) {
            this.showError('Please select a valid JSON file');
            return;
        }

        this.selectedFile = file;
        this.updateUploadArea(file.name);
        this.enableConvertButton();
        this.hideError();
    }

    updateUploadArea(fileName) {
        const uploadArea = document.getElementById('upload-area');
        uploadArea.classList.add('file-selected');
        
        const icon = uploadArea.querySelector('i');
        icon.className = 'fas fa-file-json text-4xl text-green-500';
        
        const text = uploadArea.querySelector('p');
        text.textContent = `Selected: ${fileName}`;
        
        const subText = uploadArea.querySelector('p + p');
        subText.textContent = 'Ready to convert';
    }

    enableConvertButton() {
        const convertBtn = document.getElementById('convert-btn');
        convertBtn.disabled = false;
        convertBtn.innerHTML = '<i class="fas fa-cog mr-2"></i>Convert Dashboard';
    }

    async convertDashboard() {
        if (!this.selectedFile) return;

        const formData = new FormData();
        formData.append('file', this.selectedFile);
        
        // Add conversion options
        formData.append('preserve_panel_ids', document.getElementById('preserve-panel-ids').checked);
        formData.append('convert_queries', document.getElementById('convert-queries').checked);
        formData.append('convert_visualizations', document.getElementById('convert-visualizations').checked);
        formData.append('convert_variables', document.getElementById('convert-variables').checked);
        formData.append('convert_annotations', document.getElementById('convert-annotations').checked);
        formData.append('target_kibana_version', document.getElementById('kibana-version').value);

        this.showProgress();
        this.updateProgress(0, 'Starting conversion...');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.currentFileId = result.file_id;
                this.currentJobId = result.job_id;
                this.pollProgress(result.job_id, () => {
                    this.updateProgress(100, 'Conversion completed!');
                    this.showResults(result);
                });
            } else {
                this.showError(result.error || 'Conversion failed');
                this.hideProgress();
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
            this.hideProgress();
        }
    }

    pollProgress(jobId, onComplete) {
        const poll = async () => {
            try {
                const res = await fetch(`/progress/${jobId}`);
                const data = await res.json();
                this.updateProgress(data.progress, data.status);
                if (data.progress < 100) {
                    this._progressTimeout = setTimeout(poll, 500);
                } else {
                    if (onComplete) onComplete();
                }
            } catch (e) {
                // Ignore polling errors
            }
        };
        poll();
    }

    showProgress() {
        document.getElementById('progress-section').classList.remove('hidden');
        document.getElementById('results-section').classList.add('hidden');
        document.getElementById('error-section').classList.add('hidden');
    }

    hideProgress() {
        document.getElementById('progress-section').classList.add('hidden');
    }

    updateProgress(percentage, text) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const progressTime = document.getElementById('progress-time');
        const status = document.getElementById('conversion-status');

        progressBar.style.width = `${percentage}%`;
        progressText.textContent = text;
        
        if (percentage === 100) {
            status.textContent = 'Completed';
            status.className = 'text-sm font-medium text-green-600';
        } else if (percentage > 0) {
            status.textContent = 'Processing';
            status.className = 'text-sm font-medium text-blue-600';
        }
    }

    showResults(result) {
        const resultsSection = document.getElementById('results-section');
        const summaryDiv = document.getElementById('conversion-summary');

        // Populate summary
        if (result.summary) {
            summaryDiv.innerHTML = `
                <div class="flex justify-between">
                    <span>Total Panels:</span>
                    <span class="font-medium">${result.summary.total_panels}</span>
                </div>
                <div class="flex justify-between">
                    <span>Supported Panels:</span>
                    <span class="font-medium text-green-600">${result.summary.supported_panels}</span>
                </div>
                <div class="flex justify-between">
                    <span>Unsupported Panels:</span>
                    <span class="font-medium text-red-600">${result.summary.unsupported_panels}</span>
                </div>
                <div class="flex justify-between">
                    <span>Variables:</span>
                    <span class="font-medium">${result.summary.variables}</span>
                </div>
                <div class="flex justify-between">
                    <span>Annotations:</span>
                    <span class="font-medium">${result.summary.annotations}</span>
                </div>
                <div class="flex justify-between">
                    <span>Conversion Time:</span>
                    <span class="font-medium">${result.conversion_time_ms}ms</span>
                </div>
            `;
        }

        resultsSection.classList.remove('hidden');
        this.hideProgress();
    }

    showError(message) {
        const errorSection = document.getElementById('error-section');
        const errorMessage = document.getElementById('error-message');
        
        errorMessage.textContent = message;
        errorSection.classList.remove('hidden');
        
        // Hide other sections
        document.getElementById('progress-section').classList.add('hidden');
        document.getElementById('results-section').classList.add('hidden');
    }

    hideError() {
        document.getElementById('error-section').classList.add('hidden');
    }

    downloadDashboard(format = 'json') {
        console.log('downloadDashboard called', format, this.currentFileId);
        if (!this.currentFileId) {
            console.log('No fileId set!');
            return;
        }
        let ext = format === 'ndjson' ? 'ndjson' : 'json';
        const link = document.createElement('a');
        link.href = `/download/${this.currentFileId}?format=${ext}`;
        link.download = `kibana_dashboard_${this.currentFileId}.${ext}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        console.log('Download link triggered:', link.href);
    }

    previewConversion() {
        if (!this.currentFileId) return;
        
        // Open preview in new window
        window.open(`/preview/${this.currentFileId}`, '_blank');
    }

    resetForm() {
        // Reset file selection
        this.selectedFile = null;
        this.currentFileId = null;
        this.currentJobId = null;
        
        // Reset upload area
        const uploadArea = document.getElementById('upload-area');
        uploadArea.classList.remove('file-selected');
        
        const icon = uploadArea.querySelector('i');
        icon.className = 'fas fa-cloud-upload-alt text-4xl text-gray-400';
        
        const text = uploadArea.querySelector('p');
        text.textContent = 'Drop your Grafana dashboard JSON file here';
        
        const subText = uploadArea.querySelector('p + p');
        subText.textContent = 'or click to browse';
        
        // Reset file input
        document.getElementById('file-input').value = '';
        
        // Disable convert button
        document.getElementById('convert-btn').disabled = true;
        
        // Hide all sections
        document.getElementById('progress-section').classList.add('hidden');
        document.getElementById('results-section').classList.add('hidden');
        document.getElementById('error-section').classList.add('hidden');
    }

    async checkApiStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            if (status.status !== 'healthy') {
                this.showError('API service is not available');
            }
        } catch (error) {
            console.warn('Could not check API status:', error);
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DashboardConverter();
}); 