//Toggle password visibility in Login page
export function handleLoginPasswordVisibility() {
  const toggleBtn = document.getElementById("show-login-password");
  const password = document.getElementById("login-password");

  if (!toggleBtn || !password) return;

  toggleBtn.addEventListener('click', () => {
    const eyeOff = toggleBtn.children[0];
    const eyeOn = toggleBtn.children[1];

    if (password.type === 'password') {
      password.type = 'text';
      eyeOff.classList.add('hidden')
      eyeOn.classList.remove('hidden')
    } else {
      password.type = 'password';
      eyeOn.classList.add('hidden')
      eyeOff.classList.remove('hidden')
    }
  })
}
