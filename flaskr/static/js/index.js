import { handleNavbar, handleFlashButton } from "./base.js";
import { handleLoginPasswordVisibility, handleRegisterPasswordVisibility } from "./auth.js";
import { initializeProfileUploads } from "./profile.js";

document.addEventListener('DOMContentLoaded', () => {
  initializeProfileUploads();

  handleLoginPasswordVisibility();
  handleRegisterPasswordVisibility();
  handleNavbar();
  handleFlashButton();
  console.log("DOM loaded");
});
