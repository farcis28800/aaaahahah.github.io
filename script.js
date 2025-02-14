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

    const tabs = document.querySelectorAll(".tab");
    const sections = document.querySelectorAll("section");

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

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            sections.forEach(section => section.classList.add("hidden"));
            document.getElementById(tab.dataset.tab).classList.remove("hidden");
        });
    });

    if (window.Telegram && Telegram.WebApp) {
        Telegram.WebApp.expand();
        let user = Telegram.WebApp.initDataUnsafe.user;
        if (user) {
            userId = user.id;
            document.getElementById("username").innerText = user.first_name;
            document.getElementById("avatar").src = user.photo_url || "default-avatar.png";

            let referralLink = `https://t.me/yourbot?start=${userId}`;
            referralInput.value = referralLink;
        }
    }

    copyReferralBtn.addEventListener("click", () => {
        referralInput.select();
        document.execCommand("copy");
        alert("Реферальная ссылка скопирована!");
    });

    // Обработка реферальной системы
    const urlParams = new URLSearchParams(window.location.search);
    const referrerId = urlParams.get("start");
    if (referrerId && userId !== referrerId) {
        stars += 0.0025;
        updateUI();
    }
});
