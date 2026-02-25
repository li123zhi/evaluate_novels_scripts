const { createApp } = Vue;

createApp({
    data() {
        return {
            stage: 'upload', // upload, loading, results
            isDragOver: false,
            selectedFile: null,
            dimensions: [],
            selectedDimensions: [],
            evaluationResult: null,
            errorMessage: '',
            loadingText: '正在评测中，请稍候...',
            progress: 0,
            progressText: '准备中...',
            loadingMessages: [
                '正在分析剧本内容...',
                '正在评估故事结构...',
                '正在分析人物塑造...',
                '正在评估对话质量...',
                '正在分析短剧特质...',
                '正在评估商业价值...',
                '正在生成评测报告...'
            ]
        };
    },
    computed: {
        allStrengths() {
            if (!this.evaluationResult) return [];
            const strengths = [];
            Object.values(this.evaluationResult.dimensions).forEach(dim => {
                if (dim.strengths) {
                    strengths.push(...dim.strengths);
                }
            });
            return [...new Set(strengths)].slice(0, 5);
        },
        allSuggestions() {
            if (!this.evaluationResult) return [];
            const suggestions = [];
            Object.values(this.evaluationResult.dimensions).forEach(dim => {
                if (dim.suggestions) {
                    suggestions.push(...dim.suggestions);
                }
            });
            return [...new Set(suggestions)].slice(0, 5);
        }
    },
    methods: {
        // 加载评测维度
        async loadDimensions() {
            try {
                const response = await fetch('/api/dimensions');
                const data = await response.json();
                if (data.success) {
                    this.dimensions = data.dimensions;
                    // 默认全选
                    this.selectedDimensions = this.dimensions.map(d => d.key);
                }
            } catch (error) {
                this.showError('加载评测维度失败');
            }
        },

        // 触发文件选择
        triggerFileInput() {
            this.$refs.fileInput.click();
        },

        // 处理文件选择
        handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                this.validateAndSetFile(file);
            }
        },

        // 处理拖拽
        handleDrop(event) {
            this.isDragOver = false;
            const file = event.dataTransfer.files[0];
            if (file) {
                this.validateAndSetFile(file);
            }
        },

        // 验证并设置文件
        validateAndSetFile(file) {
            // 检查文件类型
            if (!file.name.endsWith('.txt')) {
                this.showError('只支持 .txt 格式的剧本文件');
                return;
            }

            // 检查文件大小 (10MB)
            if (file.size > 10 * 1024 * 1024) {
                this.showError('文件大小不能超过 10MB');
                return;
            }

            this.selectedFile = file;
        },

        // 切换维度选择
        toggleDimension(key) {
            const index = this.selectedDimensions.indexOf(key);
            if (index > -1) {
                this.selectedDimensions.splice(index, 1);
            } else {
                this.selectedDimensions.push(key);
            }
        },

        // 全选维度
        selectAllDimensions() {
            this.selectedDimensions = this.dimensions.map(d => d.key);
        },

        // 清空维度选择
        clearAllDimensions() {
            this.selectedDimensions = [];
        },

        // 开始评测
        async startEvaluation() {
            if (!this.selectedFile) {
                this.showError('请先选择剧本文件');
                return;
            }

            if (this.selectedDimensions.length === 0) {
                this.showError('请至少选择一个评测维度');
                return;
            }

            this.stage = 'loading';
            this.progress = 0;
            this.evaluationResult = null;

            // 模拟进度更新
            this.simulateProgress();

            // 准备表单数据
            const formData = new FormData();
            formData.append('file', this.selectedFile);
            formData.append('dimensions', this.selectedDimensions.join(','));

            try {
                const response = await fetch('/api/evaluate', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    this.evaluationResult = data.result;
                    this.stage = 'results';
                    this.progress = 100;
                } else {
                    this.showError(data.error || '评测失败');
                    this.stage = 'upload';
                }
            } catch (error) {
                this.showError('网络请求失败: ' + error.message);
                this.stage = 'upload';
            }
        },

        // 模拟进度更新
        simulateProgress() {
            let currentIndex = 0;
            const interval = setInterval(() => {
                if (this.stage !== 'loading') {
                    clearInterval(interval);
                    return;
                }

                if (currentIndex < this.loadingMessages.length) {
                    this.progressText = this.loadingMessages[currentIndex];
                    this.progress = ((currentIndex + 1) / this.loadingMessages.length) * 90;
                    currentIndex++;
                }
            }, 1000);
        },

        // 重置评测
        resetEvaluation() {
            this.stage = 'upload';
            this.selectedFile = null;
            this.evaluationResult = null;
            this.progress = 0;
            this.errorMessage = '';
            // 重置文件输入
            this.$refs.fileInput.value = '';
        },

        // 下载报告
        async downloadReport() {
            if (!this.evaluationResult || !this.evaluationResult.report_files) {
                this.showError('没有可下载的报告');
                return;
            }

            // 下载 Markdown 报告
            const reportFile = this.evaluationResult.report_files.find(f => f.endsWith('.md'));
            if (reportFile) {
                try {
                    const response = await fetch(`/api/reports/${reportFile}`);
                    const data = await response.json();

                    if (data.success) {
                        // 创建下载链接
                        const blob = new Blob([data.content], { type: 'text/markdown' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = reportFile;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    }
                } catch (error) {
                    this.showError('下载报告失败');
                }
            }
        },

        // 显示错误提示
        showError(message) {
            this.errorMessage = message;
            setTimeout(() => {
                this.errorMessage = '';
            }, 5000);
        }
    },
    mounted() {
        this.loadDimensions();
    }
}).mount('#app');
