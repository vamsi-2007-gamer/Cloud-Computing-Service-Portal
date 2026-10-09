document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("fileInput");
  const uploadBtn = document.getElementById("uploadBtn");

  if (input && uploadBtn) {
    input.addEventListener("change", () => {
      uploadBtn.disabled = !input.files.length;
      if (input.files.length) {
        uploadBtn.textContent = `Upload ${input.files[0].name}`;
      } else {
        uploadBtn.textContent = "Upload";
      }
    });
  }

  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 3500);
  });
});
