/**
 * Shared JavaScript for PoE2 Tablet Tool
 * Common utilities and functions used across all pages
 */

// Get API base URL
const API = window.location.origin || "http://localhost:8001";

/**
 * Theme management
 */
const ThemeManager = {
  STORAGE_KEY: "tablet-tool-theme",

  /**
   * Initialize theme on page load
   */
  init() {
    const savedTheme = localStorage.getItem(this.STORAGE_KEY) || "dark";
    this.setTheme(savedTheme);

    // Add theme toggle button to header if it doesn't exist
    if (!document.getElementById("theme-toggle")) {
      this.addToggleButton();
    }
  },

  /**
   * Set the theme
   * @param {string} theme - 'dark' or 'light'
   */
  setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(this.STORAGE_KEY, theme);
    this.updateToggleButton();
  },

  /**
   * Toggle between dark and light themes
   */
  toggle() {
    const currentTheme = this.getCurrentTheme();
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    this.setTheme(newTheme);
  },

  /**
   * Get current theme
   * @returns {string} 'dark' or 'light'
   */
  getCurrentTheme() {
    return (
      document.documentElement.getAttribute("data-theme") ||
      localStorage.getItem(this.STORAGE_KEY) ||
      "dark"
    );
  },

  /**
   * Add theme toggle button to header
   */
  addToggleButton() {
    const header = document.querySelector("header");
    if (!header) return;

    // Check if there's already a theme-related element
    if (header.querySelector("[data-theme-action]")) return;

    const themeButton = document.createElement("button");
    themeButton.id = "theme-toggle";
    themeButton.setAttribute("data-theme-action", "toggle");
    themeButton.className = "tooltip";
    themeButton.setAttribute("data-tooltip", "Toggle theme");
    themeButton.innerHTML = "🌓";
    themeButton.style.cssText = `
            padding: 4px 8px;
            background: #2a2a2a;
            border: 1px solid #3a3a3a;
            color: #c8a96e;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 8px;
            transition: all 0.2s;
        `;
    themeButton.onclick = () => this.toggle();

    // Insert before the status element or append to header
    const statusEl = header.querySelector("#status");
    if (statusEl) {
      statusEl.before(themeButton);
    } else {
      header.appendChild(themeButton);
    }

    this.updateToggleButton();
  },

  /**
   * Update toggle button icon based on current theme
   */
  updateToggleButton() {
    const button = document.getElementById("theme-toggle");
    if (!button) return;

    const currentTheme = this.getCurrentTheme();
    button.textContent = currentTheme === "dark" ? "☀️" : "🌙";
  },
};

/**
 * Table Sorting Functionality
 * Makes table headers clickable to sort columns
 */
function initTableSorting() {
  // Add sortable class and click handlers to all sortable tables
  document.querySelectorAll("table.sortable").forEach((table) => {
    const headers = table.querySelectorAll("thead th[data-sortable]");
    headers.forEach((th, index) => {
      th.style.cursor = "pointer";
      th.style.userSelect = "none";
      th.addEventListener("click", () => {
        sortTable(table, index, th);
      });
    });
  });
}

/**
 * Sort a table by column
 * @param {HTMLElement} table - The table element
 * @param {number} columnIndex - The column index to sort by
 * @param {HTMLElement} header - The header element that was clicked
 */
function sortTable(table, columnIndex, header) {
  const tbody = table.querySelector("tbody");
  if (!tbody) return;

  const rows = Array.from(tbody.querySelectorAll("tr"));
  if (rows.length === 0) return;

  // Get current sort direction from the header
  const currentDir = header.getAttribute("data-sort-dir") || "none";
  const nextDir = currentDir === "asc" ? "desc" : "asc";

  // Remove sort indicators from all headers in this table
  table.querySelectorAll("thead th[data-sortable]").forEach((th) => {
    th.removeAttribute("data-sort-dir");
    th.textContent = th.textContent.replace(/ [↑↓]/, "");
  });

  // Set sort direction on clicked header
  header.setAttribute("data-sort-dir", nextDir);
  header.textContent += nextDir === "asc" ? " ↑" : " ↓";

  // Sort rows
  rows.sort((a, b) => {
    const aVal = a.cells[columnIndex]?.textContent.trim() || "";
    const bVal = b.cells[columnIndex]?.textContent.trim() || "";

    // Try numeric comparison first
    const aNum = parseFloat(aVal.replace(/[^\d.]/g, ""));
    const bNum = parseFloat(bVal.replace(/[^\d.]/g, ""));

    if (!isNaN(aNum) && !isNaN(bNum)) {
      return nextDir === "asc" ? aNum - bNum : bNum - aNum;
    }

    // Fall back to string comparison
    return nextDir === "asc"
      ? aVal.localeCompare(bVal)
      : bVal.localeCompare(aVal);
  });

  // Re-append sorted rows
  rows.forEach((row) => tbody.appendChild(row));
}

/**
 * Show loading overlay
 * @param {string} overlayId - The ID of the loading overlay element
 * @param {string} message - Optional message to display
 */
function showLoading(overlayId = "loading-overlay", message = "Loading...") {
  const overlay = document.getElementById(overlayId);
  if (overlay) {
    overlay.classList.add("visible");
    const loadingText = overlay.querySelector(".loading-text");
    if (loadingText && message) {
      loadingText.textContent = message;
    }
  }
}

/**
 * Hide loading overlay
 * @param {string} overlayId - The ID of the loading overlay element
 */
function hideLoading(overlayId = "loading-overlay") {
  const overlay = document.getElementById(overlayId);
  if (overlay) {
    overlay.classList.remove("visible");
  }
}

/**
 * Format a number with fixed decimal places
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted number or "—" if null/undefined
 */
function formatNumber(value, decimals = 2) {
  if (value === null || value === undefined) return "—";
  return parseFloat(value).toFixed(decimals);
}

/**
 * Strip markdown brackets from text
 * e.g., "[Mod|Name]" -> "Name"
 * @param {string} text - Text to clean
 * @returns {string} Cleaned text
 */
function stripMarkdown(text) {
  if (!text) return "";
  return text
    .replace(/\[([^|]+)\|([^\]]+)\]/g, "$2")
    .replace(/\[[^\]]+\]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Show error message with retry button
 * @param {string} message - Error message to display
 * @param {string} containerId - ID of container element
 * @param {function} onRetry - Function to call on retry
 */
function showErrorWithRetry(
  message,
  containerId = "main-container",
  onRetry = null,
) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error("Container not found:", containerId);
    return;
  }

  const existingEmpty = container.querySelector(".error-state");
  if (!existingEmpty) {
    const errorHtml = `
            <div class="empty-state error-state">
                <div class="empty-state-icon">⚠️</div>
                <div>${message}</div>
                ${onRetry ? '<button onclick="' + onRetry + '" style="margin-top: 16px; padding: 8px 16px; background: #1a1a1a; border: 1px solid #a08050; color: #c8a96e; border-radius: 4px; cursor: pointer;">Retry</button>' : ""}
            </div>
        `;
    container.innerHTML = errorHtml;
  }
}

/**
 * Show empty state message
 * @param {string} message - Message to display
 * @param {string} icon - Icon to show (default: "ℹ️")
 * @param {string} containerId - ID of container element
 */
function showEmptyState(message, icon = "ℹ️", containerId = "main-container") {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error("Container not found:", containerId);
    return;
  }

  const existingEmpty = container.querySelector(".empty-state");
  if (!existingEmpty) {
    const emptyHtml = `
            <div class="empty-state">
                <div class="empty-state-icon">${icon}</div>
                <div>${message}</div>
            </div>
        `;
    container.innerHTML = emptyHtml;
  }
}

/**
 * Update timestamp display
 * @param {string} elementId - ID of the timestamp element
 */
function updateTimestamp(elementId = "last-updated") {
  const now = new Date();
  const timeStr = now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = timeStr;
  }
}

/**
 * Tablet color mapping for charts
 */
const TABLET_COLORS = {
  ritual: "#c8a96e",
  breach: "#8ab4e8",
  abyss: "#7a9e7a",
  delirium: "#a870a8",
  overseer: "#cc9966",
  irradiated: "#e87878",
  temple: "#70a8a8",
  expedition: "#a8a870",
};

/**
 * Common color palette
 */
const COLORS = [
  "#c8a96e",
  "#8ab4e8",
  "#7a9e7a",
  "#cc9966",
  "#a870a8",
  "#70a8a8",
  "#e87878",
  "#a8a870",
];

/**
 * Tablet icon mapping
 */
const TABLET_ICONS = {
  irradiated: "☢️",
  abyss: "🕳️",
  breach: "💥",
  delirium: "👁️",
  expedition: "🗺️",
  overseer: "👁️",
  ritual: "⚰️",
  temple: "🏛️",
};

/**
 * Show copied to clipboard notification
 * @param {string} message - Message to display
 */
function showCopiedNotification(message = "Copied to clipboard!") {
  let notification = document.getElementById("copied-notification");
  if (!notification) {
    notification = document.createElement("div");
    notification.id = "copied-notification";
    notification.className = "copied-notification";
    notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2a2a2a;
            border: 1px solid #a08050;
            color: #c8a96e;
            padding: 10px 16px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;
    document.body.appendChild(notification);

    // Add animation keyframes if not exists
    if (!document.getElementById("slideIn-animation")) {
      const style = document.createElement("style");
      style.id = "slideIn-animation";
      style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
      document.head.appendChild(style);
    }

    setTimeout(() => notification.remove(), 2000);
  } else {
    notification.textContent = message;
    clearTimeout(notification._timer);
    notification._timer = setTimeout(() => notification.remove(), 2000);
  }
  notification.textContent = message;
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @param {string} successMessage - Message to show on success
 */
async function copyToClipboard(text, successMessage = "Copied to clipboard!") {
  try {
    await navigator.clipboard.writeText(text);
    showCopiedNotification(successMessage);
    return true;
  } catch (e) {
    console.error("Failed to copy:", e);
    showCopiedNotification("Failed to copy: " + e.message);
    return false;
  }
}

/**
 * Export table data to CSV
 * @param {HTMLElement} table - The table element to export
 * @param {string} filename - The filename for the CSV
 */
function exportTableToCSV(table, filename = "table-data.csv") {
  const headers = Array.from(table.querySelectorAll("thead th")).map((th) =>
    th.textContent.trim(),
  );
  const rows = Array.from(table.querySelectorAll("tbody tr"));

  const csvContent = [
    headers.join(","),
    ...rows.map((row) =>
      Array.from(row.cells)
        .map((cell) => {
          const text = cell.textContent.trim();
          // Escape quotes and wrap in quotes if contains comma
          return text.includes(",") || text.includes('"') || text.includes("\n")
            ? `"${text.replace(/"/g, '""')}"`
            : text;
        })
        .join(","),
    ),
  ].join("\n");

  downloadFile(csvContent, filename, "text/csv");
}

/**
 * Export table data to JSON
 * @param {HTMLElement} table - The table element to export
 * @param {string} filename - The filename for the JSON
 */
function exportTableToJSON(table, filename = "table-data.json") {
  const headers = Array.from(table.querySelectorAll("thead th")).map((th) =>
    th.textContent.trim(),
  );
  const rows = Array.from(table.querySelectorAll("tbody tr"));

  const data = rows.map((row) => {
    const obj = {};
    Array.from(row.cells).forEach((cell, i) => {
      obj[headers[i]] = cell.textContent.trim();
    });
    return obj;
  });

  downloadFile(JSON.stringify(data, null, 2), filename, "application/json");
}

/**
 * Download a file
 * @param {string} content - The file content
 * @param {string} filename - The filename
 * @param {string} mimeType - The MIME type
 */
function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Add export buttons to all sortable tables
 */
function addExportButtons() {
  document.querySelectorAll("table.sortable").forEach((table) => {
    // Check if export buttons already exist
    const existingButtons = table.querySelector(".export-buttons");
    if (existingButtons) return;

    const container = document.createElement("div");
    container.className = "export-buttons";
    container.style.cssText = "display: flex; gap: 8px; margin-top: 8px;";

    const csvButton = document.createElement("button");
    csvButton.innerHTML = "📥 CSV";
    csvButton.title = "Export to CSV";
    csvButton.style.cssText = "padding: 4px 8px; font-size: 11px;";
    csvButton.onclick = () => {
      const tableName = table.id || "table";
      exportTableToCSV(table, `${tableName}.csv`);
    };

    const jsonButton = document.createElement("button");
    jsonButton.innerHTML = "📥 JSON";
    jsonButton.title = "Export to JSON";
    jsonButton.style.cssText = "padding: 4px 8px; font-size: 11px;";
    jsonButton.onclick = () => {
      const tableName = table.id || "table";
      exportTableToJSON(table, `${tableName}.json`);
    };

    container.appendChild(csvButton);
    container.appendChild(jsonButton);

    // Insert after the table
    table.parentNode.insertBefore(container, table.nextSibling);
  });
}

// Add export buttons when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    ThemeManager.init();
    initTableSorting();
    addExportButtons();
  });
} else {
  ThemeManager.init();
  initTableSorting();
  addExportButtons();
}
