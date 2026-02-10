export function initializeProfileUploads() {
  const avatarWrapper = document.getElementById("avatar-upload-wrapper");
  const coverWrapper = document.getElementById("cover-upload-wrapper");

  if (!avatarWrapper || !coverWrapper) {
    return;
  }

  const avatarInput = document.getElementById("avatar-input");
  const avatarPreview = document.getElementById("avatar-preview");
  const avatarPlaceholder = document.getElementById("avatar-placeholder");
  const avatarButton = document.getElementById("avatar-button");
  const avatarFileName = document.getElementById("avatar-filename");
  const avatarRemove = document.getElementById("avatar-remove");

  avatarButton.addEventListener("click", () => avatarInput.click());

  avatarInput.addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
        avatarPreview.src = e.target.result;
        avatarPreview.classList.remove("hidden");
        avatarPlaceholder.classList.add("hidden");
        avatarFileName.textContent = file.name;
        avatarFileName.classList.remove("hidden");
        avatarRemove.classList.remove("hidden");
      };
      reader.readAsDataURL(file);
    }
  });

  avatarRemove.addEventListener("click", function () {
    avatarInput.value = "";
    avatarPreview.src = "";
    avatarPreview.classList.add("hidden");
    avatarPlaceholder.classList.remove("hidden");
    avatarFileName.classList.add("hidden");
    avatarRemove.classList.add("hidden");
  });

  const coverInput = document.getElementById("cover-input");
  const coverPreview = document.getElementById("cover-preview");
  const coverPlaceholder = document.getElementById("cover-placeholder");
  const coverButton = document.getElementById("cover-button");
  const coverFileName = document.getElementById("cover-filename");
  const coverRemove = document.getElementById("cover-remove");

  coverButton.addEventListener("click", () => coverInput.click());

  coverInput.addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
        coverPreview.src = e.target.result;
        coverPreview.classList.remove("hidden");
        coverPlaceholder.classList.add("hidden");
        coverFileName.textContent = file.name;
        coverFileName.classList.remove("hidden");
        coverRemove.classList.remove("hidden");
      };
      reader.readAsDataURL(file);
    }
  });

  coverRemove.addEventListener("click", function () {
    coverInput.value = "";
    coverPreview.src = "";
    coverPreview.classList.add("hidden");
    coverPlaceholder.classList.remove("hidden");
    coverFileName.classList.add("hidden");
    coverRemove.classList.add("hidden");
  });

  console.log("Profile uploads initialized");
}
