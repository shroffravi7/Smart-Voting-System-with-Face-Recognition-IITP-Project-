let stream = null;
const video = document.getElementById("camera");
const status = document.getElementById("cameraStatus");
const startBtn = document.getElementById("startCamera");
const verifyBtn = document.getElementById("verifyBtn");

startBtn.addEventListener("click", async () => {
  try {
    if (!navigator.mediaDevices?.getUserMedia) {
      status.textContent = "Camera access is not supported by this browser/context.";
      return;
    }

    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
      audio: false
    });
    video.srcObject = stream;
    await video.play();
    status.textContent = "Camera active. Position one face inside the frame.";
  } catch (error) {
    console.error("Camera error:", error);
    status.textContent = "Camera permission was denied or unavailable.";
  }
});

verifyBtn.addEventListener("click", async () => {
  if (!stream) {
    alert("Start the camera first.");
    return;
  }

  if (!video.videoWidth || !video.videoHeight) {
    alert("Camera is still starting. Please wait a moment and try again.");
    return;
  }

  const canvas = document.getElementById("snapshot");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  status.textContent = "Verifying face...";
  verifyBtn.disabled = true;

  try {
    // The voter is already identified by the server-side sign-in session.
    // Do not read a non-existent voterId input from the verification page.
    const response = await fetch(window.SMARTVOTE.verifyUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image: canvas.toDataURL("image/jpeg", 0.9)
      })
    });

    const data = await response.json();
    if (data.ok) {
      status.textContent = "Face verified. Opening ballot...";
      window.location = data.redirect;
    } else {
      status.textContent = data.message || "Verification failed.";
    }
  } catch (error) {
    console.error("Verification error:", error);
    status.textContent = "Could not contact the server. Please try again.";
  } finally {
    verifyBtn.disabled = false;
  }
});

window.addEventListener("beforeunload", () => {
  if (stream) stream.getTracks().forEach(track => track.stop());
});
