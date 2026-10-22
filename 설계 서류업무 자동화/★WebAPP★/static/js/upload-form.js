"use strict";

function wireGenerateForm(formId, endpoint, submitLabel) {
  const form = document.getElementById(formId);
  const msgArea = document.getElementById("msg-area");
  const submitBtn = document.getElementById("submit-btn");
  const defaultLabel = submitBtn.textContent;

  function showMsg(text, type) {
    msgArea.innerHTML = `<div class="msg ${type}">${text}</div>`;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgArea.innerHTML = "";
    submitBtn.disabled = true;
    submitBtn.textContent = "생성 중... (파일 크기/개수에 따라 시간이 걸릴 수 있습니다)";

    try {
      const formData = new FormData(form);
      const res = await fetch(endpoint, { method: "POST", body: formData });

      if (!res.ok) {
        let errText = "생성에 실패했습니다.";
        try { const data = await res.json(); errText = data.error || errText; } catch (e) {}
        showMsg(errText, "error");
        return;
      }

      const warningsB64 = res.headers.get("X-Warnings-B64");
      const blob = await res.blob();

      let filename = "결과.xlsx";
      const disposition = res.headers.get("Content-Disposition");
      if (disposition) {
        const match = disposition.match(/filename\*=UTF-8''([^;]+)/) || disposition.match(/filename="?([^";]+)"?/);
        if (match) filename = decodeURIComponent(match[1]);
      }

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = filename;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);

      if (warningsB64) {
        const text = decodeURIComponent(escape(atob(warningsB64)));
        showMsg("파일은 생성되었지만 일부 경고가 있습니다:\n\n" + text, "warn");
      } else {
        showMsg("생성 완료! 다운로드된 파일을 확인하세요.", "ok");
      }
    } catch (err) {
      showMsg("오류가 발생했습니다: " + err, "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = submitLabel || defaultLabel;
    }
  });
}
