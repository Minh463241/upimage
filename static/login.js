// login.js

document.addEventListener("DOMContentLoaded", function() {
  const loginForm = document.getElementById("loginForm");
  const registerBtn = document.getElementById("registerBtn");

  // Xử lý khi nhấn nút Sign In (submit form)
  loginForm.addEventListener("submit", function(e) {
    e.preventDefault(); // Ngăn form reload trang
  
    // Lấy giá trị email và password
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
  
    // Gửi yêu cầu đăng nhập lên server (sử dụng fetch)
    fetch('/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        window.location.href = '/'; // chuyển hướng khi đăng nhập thành công
      } else {
        alert(data.message || 'Đăng nhập thất bại.');
      }
    })
    .catch(err => {
      console.error('Lỗi khi đăng nhập:', err);
      alert('Có lỗi xảy ra. Vui lòng thử lại.');
    });
  });
  

  // Xử lý khi nhấn nút Register
  registerBtn.addEventListener("click", function() {
    // Redirect tới trang đăng ký hoặc thực hiện hành động đăng ký khác
    alert("Redirecting to registration page...");
    // Ví dụ: window.location.href = '/register';
  });
});
