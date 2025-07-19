// 系统配置文件
const CONFIG = {
    // API 配置
    API: {
        BASE_URL: 'http://localhost:5000/api',
        TIMEOUT: 30000, // 30秒超时
        RETRY_COUNT: 3,
        RETRY_DELAY: 1000 // 重试延迟1秒
    },

    // 文件上传配置
    UPLOAD: {
        MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
        MAX_FILES_COUNT: 50, // 最多同时上传50个文件
        ALLOWED_TYPES: [
            'txt', 'pdf', 'doc', 'docx', 'md',
            'jpg', 'jpeg', 'png', 'gif', 'svg',
            'xls', 'xlsx', 'ppt', 'pptx',
            'zip', 'rar', '7z'
        ],
        CHUNK_SIZE: 1024 * 1024 // 1MB 分块大小
    },

    // UI 配置
    UI: {
        DEBOUNCE_DELAY: 300, // 防抖延迟
        THROTTLE_DELAY: 100, // 节流延迟
        MESSAGE_DURATION: 3000, // 消息显示时长
        ANIMATION_DURATION: 200, // 动画时长
        PAGINATION_SIZE: 20, // 分页大小
        SEARCH_MIN_LENGTH: 2 // 搜索最小长度
    },

    // 存储配置
    STORAGE: {
        PREFIX: 'ai_resume_', // 存储前缀
        EXPIRE_TIME: 7 * 24 * 60 * 60 * 1000, // 7天过期
        KEYS: {
            APP_STATE: 'app_state',
            USER_SETTINGS: 'user_settings',
            RECENT_PROJECTS: 'recent_projects',
            THEME: 'theme'
        }
    },

    // 默认值
    DEFAULTS: {
        PROJECT_NAME: '默认项目',
        PROJECT_DESCRIPTION: '系统自动创建的默认项目',
        PAGE_SIZE: 20,
        THEME: 'light'
    },

    // 系统限制
    LIMITS: {
        PROJECT_NAME_MAX_LENGTH: 100,
        PROJECT_DESC_MAX_LENGTH: 500,
        FILE_NAME_MAX_LENGTH: 255,
        SEARCH_RESULTS_MAX: 100
    },

    // 状态码
    STATUS_CODES: {
        SUCCESS: 200,
        CREATED: 201,
        NO_CONTENT: 204,
        BAD_REQUEST: 400,
        UNAUTHORIZED: 401,
        FORBIDDEN: 403,
        NOT_FOUND: 404,
        INTERNAL_ERROR: 500
    },

    // 错误消息
    ERROR_MESSAGES: {
        NETWORK_ERROR: '网络连接失败，请检查网络设置',
        SERVER_ERROR: '服务器内部错误，请稍后重试',
        UNAUTHORIZED: '未授权访问，请重新登录',
        NOT_FOUND: '请求的资源不存在',
        VALIDATION_ERROR: '数据验证失败',
        UPLOAD_ERROR: '文件上传失败',
        DOWNLOAD_ERROR: '文件下载失败',
        DELETE_ERROR: '删除操作失败',
        UNKNOWN_ERROR: '未知错误'
    },

    // 成功消息
    SUCCESS_MESSAGES: {
        PROJECT_CREATED: '项目创建成功',
        PROJECT_UPDATED: '项目更新成功',
        PROJECT_DELETED: '项目删除成功',
        FILE_UPLOADED: '文件上传成功',
        FILE_DOWNLOADED: '文件下载成功',
        FILE_DELETED: '文件删除成功',
        DATA_SAVED: '数据保存成功',
        DATA_EXPORTED: '数据导出成功'
    },

    // 页面配置
    PAGES: {
        'project-detail': {
            name: '项目管理',
            icon: '🗂️',
            description: '管理项目和文件'
        },
        'dashboard': {
            name: '仪表板',
            icon: '📊',
            description: '查看系统统计信息'
        },
        'resumes': {
            name: '简历管理',
            icon: '📋',
            description: '管理简历数据'
        },
        'analytics': {
            name: '数据分析',
            icon: '📈',
            description: '分析数据趋势'
        },
        'knowledge': {
            name: '知识库',
            icon: '📚',
            description: '知识库管理'
        },
        'settings': {
            name: '系统设置',
            icon: '⚙️',
            description: '系统配置设置'
        }
    },

    // 文件类型图标映射
    FILE_ICONS: {
        'pdf': '📑',
        'doc': '📝',
        'docx': '📝',
        'txt': '📄',
        'md': '📝',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'svg': '🖼️',
        'xls': '📊',
        'xlsx': '📊',
        'ppt': '📈',
        'pptx': '📈',
        'zip': '🗜️',
        'rar': '🗜️',
        '7z': '🗜️',
        'mp4': '🎥',
        'avi': '🎥',
        'mov': '🎥',
        'mp3': '🎵',
        'wav': '🎵',
        'flac': '🎵',
        'default': '📄'
    },

    // 主题配置
    THEMES: {
        light: {
            name: '浅色主题',
            primary: '#1a73e8',
            secondary: '#f8f9fa',
            background: '#ffffff',
            text: '#333333'
        },
        dark: {
            name: '深色主题',
            primary: '#4285f4',
            secondary: '#2d2d2d',
            background: '#1a1a1a',
            text: '#ffffff'
        }
    },

    // 快捷键配置
    SHORTCUTS: {
        'ctrl+r': 'refreshData',
        'ctrl+n': 'newProject',
        'ctrl+u': 'uploadFile',
        'ctrl+s': 'saveData',
        'ctrl+e': 'exportData',
        'escape': 'closeModal',
        'f5': 'reload'
    },

    // 开发模式配置
    DEV: {
        DEBUG: true,
        CONSOLE_LOG: true,
        MOCK_DATA: false,
        SHOW_PERFORMANCE: false
    },

    // 生产模式配置
    PROD: {
        DEBUG: false,
        CONSOLE_LOG: false,
        MOCK_DATA: false,
        SHOW_PERFORMANCE: false
    }
};

// 根据环境切换配置
const ENV = 'dev'; // 'dev' 或 'prod'
const CURRENT_CONFIG = ENV === 'dev' ? CONFIG.DEV : CONFIG.PROD;

// 合并环境配置
Object.assign(CONFIG, CURRENT_CONFIG);

// 导出配置
if (typeof window !== 'undefined') {
    window.CONFIG = CONFIG;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}