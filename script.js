document.addEventListener("DOMContentLoaded", () => {
    let stars = parseFloat(localStorage.getItem("stars")) || 0.0001;
    let energy = parseFloat(localStorage.getItem("energy")) || 100;
    let energyMax = 100;
    let userId = null;

    const starButton = document.getElementById("star-button");
    const starsCounter = document.getElementById("stars-counter");
    const energyBar = document.getElementById("energy-fill");
    const referralInput = document.getElementById("referral-link");
    const copyReferralBtn = document.getElementById("copy-referral");

    function updateUI() {
        starsCounter.innerText = `⭐ ${stars.toFixed(4)}`;
        energyBar.style.width = `${(energy / energyMax) * 100}%`;

        localStorage.setItem("stars", stars);
        localStorage.setItem("energy", energy);
    }

    starButton.addEventListener("click", () => {
        if (energy > 0) {
            stars += 0.0001;
            energy--;
            updateUI();
        }
    });

    setInterval(() => {
        if (energy < energyMax) {
            energy++;
            updateUI();
        }
    }, 500);

    if (window.Telegram && Telegram.WebApp) {
        Telegram.WebApp.expand();
        Telegram.WebApp.ready();

        let user = Telegram.WebApp.initDataUnsafe.user;
        if (user) {
            userId = user.id;
            document.getElementById("username").innerText = user.first_name;
            document.getElementById("avatar").src = user.photo_url || "default-avatar.png";

            let referralLink = `https://t.me/YOUR_BOT_USERNAME?start=${userId}`;
            referralInput.value = referralLink;
        }
    }

    copyReferralBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(referralInput.value);
        alert("Реферальная ссылка скопирована!");
    });

    // Проверяем, есть ли реферальный код в URL
    const urlParams = new URLSearchParams(window.location.search);
    const referrerId = urlParams.get("start");
    if (referrerId && (!localStorage.getItem("ref-earned") || localStorage.getItem("ref-earned") !== referrerId)) {
        stars += 0.0025;
        localStorage.setItem("ref-earned", referrerId);
        updateUI();
    }
});
