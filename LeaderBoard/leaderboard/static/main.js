// Countdown timer for January 23, 1:00 PM Rome Time
document.addEventListener('DOMContentLoaded', function () {
    const targetDate = new Date('2025-01-28T13:00:00+01:00'); // January 23, 1:00 PM Rome Time (CET)
    const timerElement = document.getElementById('countdown-timer');

    function updateCountdown() {
        const now = new Date();
        const timeDifference = targetDate - now;

        if (timeDifference <= 0) {
            timerElement.innerHTML = "ePIC AI/ML Session has ended!";
            clearInterval(interval);
            return;
        }

        const days = Math.floor(timeDifference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeDifference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeDifference % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeDifference % (1000 * 60)) / 1000);

        timerElement.innerHTML = `Countdown until end: ${days}d ${hours}h ${minutes}m ${seconds}s`;
    }

    const interval = setInterval(updateCountdown, 1000);
});
