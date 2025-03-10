#pragma once

#include <string>
#include <memory>

// Include pybind11 for Python integration
#include <pybind11/pybind11.h>

// Include spdlog if available
#ifndef WITH_SPDLOG
#define WITH_SPDLOG
#endif

#ifdef WITH_SPDLOG
#include <spdlog/spdlog.h>
#endif

namespace dem_bones {

namespace py = pybind11;

/**
 * @brief Log levels
 */
enum class LogLevel {
    TRACE,
    DEBUG,
    INFO,
    WARN,
    ERROR,
    CRITICAL
};

/**
 * @brief DemBones Logger class
 *
 * Provides C++ and Python logging integration
 */
class Logger {
public:
    /**
     * @brief Get logger instance (singleton pattern)
     */
    static Logger& instance() {
        static Logger instance;
        return instance;
    }

    /**
     * @brief Initialize logging system
     * 
     * @param level Log level
     * @param to_console Whether to output to console
     * @param to_python Whether to forward to Python
     */
    void init(LogLevel level = LogLevel::INFO, bool to_console = true, bool to_python = true) {
        m_level = level;
        m_to_console = to_console;
        m_to_python = to_python;

#ifdef WITH_SPDLOG
        // Configure spdlog
        if (to_console) {
            spdlog::set_level(convert_level(level));
            m_logger = spdlog::default_logger();
        }
#endif
    }

    /**
     * @brief Log trace level message
     */
    void trace(const std::string& message) {
        log(LogLevel::TRACE, message);
    }

    /**
     * @brief Log debug level message
     */
    void debug(const std::string& message) {
        log(LogLevel::DEBUG, message);
    }

    /**
     * @brief Log info level message
     */
    void info(const std::string& message) {
        log(LogLevel::INFO, message);
    }

    /**
     * @brief Log warning level message
     */
    void warn(const std::string& message) {
        log(LogLevel::WARN, message);
    }

    /**
     * @brief Log error level message
     */
    void error(const std::string& message) {
        log(LogLevel::ERROR, message);
    }

    /**
     * @brief Log critical level message
     */
    void critical(const std::string& message) {
        log(LogLevel::CRITICAL, message);
    }

    /**
     * @brief Set log level
     */
    void set_level(LogLevel level) {
        m_level = level;
#ifdef WITH_SPDLOG
        spdlog::set_level(convert_level(level));
#endif
    }

private:
    // Private constructor (singleton pattern)
    Logger() : m_level(LogLevel::INFO), m_to_console(true), m_to_python(false) {}

    // Disable copy and assignment
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    /**
     * @brief Log a message
     * 
     * @param level Log level
     * @param message Log message
     */
    void log(LogLevel level, const std::string& message) {
        if (level < m_level) {
            return;
        }

#ifdef WITH_SPDLOG
        // Use spdlog to log to console
        if (m_to_console && m_logger) {
            switch (level) {
                case LogLevel::TRACE:
                    m_logger->trace(message);
                    break;
                case LogLevel::DEBUG:
                    m_logger->debug(message);
                    break;
                case LogLevel::INFO:
                    m_logger->info(message);
                    break;
                case LogLevel::WARN:
                    m_logger->warn(message);
                    break;
                case LogLevel::ERROR:
                    m_logger->error(message);
                    break;
                case LogLevel::CRITICAL:
                    m_logger->critical(message);
                    break;
            }
        }
#endif

        // Forward to Python
        if (m_to_python) {
            log_to_python(level, message);
        }
    }

    /**
     * @brief Forward log to Python
     * 
     * @param level Log level
     * @param message Log message
     */
    void log_to_python(LogLevel level, const std::string& message) {
        // Acquire Python GIL
        py::gil_scoped_acquire acquire;
        
        try {
            // Import Python logging module
            py::module logging = py::module::import("logging");
            py::object logger = logging.attr("getLogger")("dem_bones");
            
            // Call appropriate log method based on level
            switch (level) {
                case LogLevel::TRACE:
                case LogLevel::DEBUG:
                    logger.attr("debug")(message);
                    break;
                case LogLevel::INFO:
                    logger.attr("info")(message);
                    break;
                case LogLevel::WARN:
                    logger.attr("warning")(message);
                    break;
                case LogLevel::ERROR:
                    logger.attr("error")(message);
                    break;
                case LogLevel::CRITICAL:
                    logger.attr("critical")(message);
                    break;
            }
        } catch (const py::error_already_set& e) {
            // Python exception handling
#ifdef WITH_SPDLOG
            if (m_logger) {
                m_logger->error("Failed to log to Python: {}", e.what());
            }
#endif
        }
    }

#ifdef WITH_SPDLOG
    /**
     * @brief Convert log level
     * 
     * @param level Internal log level
     * @return spdlog log level
     */
    spdlog::level::level_enum convert_level(LogLevel level) {
        switch (level) {
            case LogLevel::TRACE:
                return spdlog::level::trace;
            case LogLevel::DEBUG:
                return spdlog::level::debug;
            case LogLevel::INFO:
                return spdlog::level::info;
            case LogLevel::WARN:
                return spdlog::level::warn;
            case LogLevel::ERROR:
                return spdlog::level::err;
            case LogLevel::CRITICAL:
                return spdlog::level::critical;
            default:
                return spdlog::level::info;
        }
    }
#endif

    LogLevel m_level;                  // Current log level
    bool m_to_console;                 // Whether to output to console
    bool m_to_python;                  // Whether to forward to Python

#ifdef WITH_SPDLOG
    std::shared_ptr<spdlog::logger> m_logger;  // spdlog logger instance
#endif
};

} // namespace dem_bones
