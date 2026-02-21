import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 120_000, // 2 min — LLM calls can be slow on large chats
});

/**
 * Upload a WhatsApp .txt export file.
 * @param {File} file
 * @param {(pct: number) => void} [onProgress]
 * @returns {Promise<{ filename: string, sales: object[], errors: object[] }>}
 */
export async function uploadChat(file, onProgress) {
  const form = new FormData();
  form.append("file", file);

  const { data } = await api.post("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });

  return data;
}

/**
 * Request an Excel file for the given sales array.
 * Triggers a browser download.
 * @param {object[]} sales
 */
export async function exportToExcel(sales) {
  const response = await api.post(
    "/export",
    { sales },
    { responseType: "blob" }
  );

  const url = URL.createObjectURL(response.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sales_export.xlsx";
  a.click();
  URL.revokeObjectURL(url);
}

export default api;
