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
      eyeOff.classList.add('hidden');
      eyeOn.classList.remove('hidden');
    } else {
      password.type = 'password';
      eyeOn.classList.add('hidden');
      eyeOff.classList.remove('hidden');
    }
  })
}

//Toggle password visibility in Register page
export function handleRegisterPasswordVisibility() {
  const toggleBtn = document.getElementById("show-register-password");
  const toggleBtn2 = document.getElementById("show-repeat-register-password");
  const password = document.getElementById("register-password");
  const password2 = document.getElementById("repeat-register-password");

  if (!toggleBtn || !toggleBtn2 || !password || !password2) return;

  toggleBtn.addEventListener('click', () => {
    const eyeOff = toggleBtn.children[0];
    const eyeOn = toggleBtn.children[1];

    if (password.type === 'password') {
      password.type = 'text';
      eyeOff.classList.add('hidden');
      eyeOn.classList.remove('hidden');
    } else {
      password.type = 'password';
      eyeOn.classList.add('hidden');
      eyeOff.classList.remove('hidden');
    }
  })

  toggleBtn2.addEventListener('click', () => {
    const eyeOff = toggleBtn2.children[0];
    const eyeOn = toggleBtn2.children[1];

    if (password2.type === 'password') {
      password2.type = 'text';
      eyeOff.classList.add('hidden');
      eyeOn.classList.remove('hidden');
    } else {
      password2.type = 'password';
      eyeOn.classList.add('hidden');
      eyeOff.classList.remove('hidden');
    }
  })
}

//Toggle password visibility in Reset password page
export function handleResetPasswordVisibility() {
  const toggleBtn = document.getElementById("show-reset-password");
  const toggleBtn2 = document.getElementById("show-repeat-reset-password");
  const password = document.getElementById("reset-password");
  const password2 = document.getElementById("repeat-reset-password");

  if (!toggleBtn || !toggleBtn2 || !password || !password2) return;

  toggleBtn.addEventListener('click', () => {
    const eyeOff = toggleBtn.children[0];
    const eyeOn = toggleBtn.children[1];

    if (password.type === 'password') {
      password.type = 'text';
      eyeOff.classList.add('hidden');
      eyeOn.classList.remove('hidden');
    } else {
      password.type = 'password';
      eyeOn.classList.add('hidden');
      eyeOff.classList.remove('hidden');
    }
  })

  toggleBtn2.addEventListener('click', () => {
    const eyeOff = toggleBtn2.children[0];
    const eyeOn = toggleBtn2.children[1];

    if (password2.type === 'password') {
      password2.type = 'text';
      eyeOff.classList.add('hidden');
      eyeOn.classList.remove('hidden');
    } else {
      password2.type = 'password';
      eyeOn.classList.add('hidden');
      eyeOff.classList.remove('hidden');
    }
  })
}
