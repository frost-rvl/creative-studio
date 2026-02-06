import { handleNavbar, handleFlashButton } from "./base.js";
import { handleLoginPasswordVisibility, handleRegisterPasswordVisibility, handleResetPasswordVisibility } from "./auth.js";
import { initializeProfileUploads } from "./profile.js";

document.addEventListener('DOMContentLoaded', () => {
  initializeProfileUploads();

  handleLoginPasswordVisibility();
  handleRegisterPasswordVisibility();
  handleResetPasswordVisibility();

  handleNavbar();
  handleFlashButton();
  console.log("DOM loaded");
});
