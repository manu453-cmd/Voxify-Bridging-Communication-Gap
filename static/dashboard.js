// Profile Dropdown
const profileBtn = document.querySelector(".profile-btn");
const dropdownContent = document.querySelector(".dropdown-content");

profileBtn.addEventListener("click", () => {
  dropdownContent.classList.toggle("active");
});

document.addEventListener("click", (e) => {
  if (!profileBtn.contains(e.target)) {
    dropdownContent.classList.remove("active");
  }
});

// Modal Handling
const modal = document.getElementById("profile-modal");
const editProfileBtn = document.getElementById("edit-profile");
const closeModal = document.querySelector(".close-modal");

editProfileBtn.addEventListener("click", (e) => {
  e.preventDefault();
  modal.classList.add("active");
});

closeModal.addEventListener("click", () => {
  modal.classList.remove("active");
});

// Conversion Mode Selection
const conversionCards = document.querySelectorAll(".conversion-card");
const conversionInterface = document.querySelector(".conversion-interface");
const conversionContent = document.querySelector(".conversion-content");
const backBtn = document.querySelector(".back-btn");

conversionCards.forEach((card) => {
  card.addEventListener("click", () => {
    const mode = card.dataset.mode;
    loadConversionInterface(mode);
  });
});

backBtn.addEventListener("click", () => {
  conversionInterface.style.display = "none";
  document.querySelector(".conversion-grid").style.display = "grid";
});

function loadConversionInterface(mode) {
  document.querySelector(".conversion-grid").style.display = "none";
  conversionInterface.style.display = "block";

  // Load appropriate interface based on mode
  switch (mode) {
    case "text-to-speech":
      conversionContent.innerHTML = createTextToSpeechInterface();
      break;
    case "speech-to-text":
      conversionContent.innerHTML = createSpeechToTextInterface();
      break;
    case "text-to-braille":
      conversionContent.innerHTML = createTextToBrailleInterface();
      break;
    case "braille-to-speech":
      conversionContent.innerHTML = createBrailleToSpeechInterface();
      break;
  }

  // Initialize the interface
  initializeInterface(mode);
}

function createTextToSpeechInterface() {
  return `
        <h2>Text to Speech Converter</h2>
        <div class="converter-container">
            <textarea class="converter-input" placeholder="Enter text to convert to speech..."></textarea>
            <button class="btn btn-primary convert-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                Convert to Speech
            </button>
        </div>
    `;
}

function createSpeechToTextInterface() {
  return `
        <h2>Speech to Text Converter</h2>
        <div class="converter-container">
            <button class="btn btn-primary record-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                </svg>
                Start Recording
            </button>
            <div class="transcription-output"></div>
        </div>
    `;
}

function createTextToBrailleInterface() {
  return `
        <h2>Text to Braille Converter</h2>
        <div class="converter-container">
            <textarea class="converter-input" placeholder="Enter text to convert to Braille..."></textarea>
            <button class="btn btn-primary convert-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="6" cy="6" r="3"></circle>
                    <circle cx="6" cy="18" r="3"></circle>
                    <circle cx="18" cy="6" r="3"></circle>
                    <circle cx="18" cy="18" r="3"></circle>
                </svg>
                Convert to Braille
            </button>
            <div class="braille-output"></div>
        </div>
    `;
}

function createBrailleToSpeechInterface() {
  return `
        <h2>Braille to Speech Converter</h2>
        <div class="converter-container">
            <div class="braille-input-grid"></div>
            <button class="btn btn-primary convert-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                Convert to Speech
            </button>
        </div>
    `;
}

function initializeInterface(mode) {
  // Add event listeners and initialize functionality based on mode
  switch (mode) {
    case "text-to-speech":
      initTextToSpeech();
      break;
    case "speech-to-text":
      initSpeechToText();
      break;
    case "text-to-braille":
      initTextToBraille();
      break;
    case "braille-to-speech":
      initBrailleToSpeech();
      break;
  }
}

// Initialize specific conversion interfaces
function initTextToSpeech() {
  const convertBtn = document.querySelector(".convert-btn");
  const input = document.querySelector(".converter-input");

  convertBtn.addEventListener("click", async () => {
    const text = input.value;
    try {
      const response = await fetch("/api/text-to-speech", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (error) {
      console.error("Error converting text to speech:", error);
    }
  });
}

function initSpeechToText() {
  const recordBtn = document.querySelector(".record-btn");
  const output = document.querySelector(".transcription-output");
  let isRecording = false;

  recordBtn.addEventListener("click", () => {
    if (!isRecording) {
      // Start recording
      recordBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                </svg>
                Stop Recording
            `;
      isRecording = true;
    } else {
      // Stop recording
      recordBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                </svg>
                Start Recording
            `;
      isRecording = false;
    }
  });
}

function initTextToBraille() {
  const convertBtn = document.querySelector(".convert-btn");
  const input = document.querySelector(".converter-input");
  const output = document.querySelector(".braille-output");

  convertBtn.addEventListener("click", async () => {
    const text = input.value;
    try {
      const response = await fetch("/api/text-to-braille", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      output.textContent = data.braille;
    } catch (error) {
      console.error("Error converting text to braille:", error);
    }
  });
}

function initBrailleToSpeech() {
  // Initialize Braille input grid and conversion logic
}
