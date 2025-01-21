// static/main.js

document.addEventListener('DOMContentLoaded', function() {
    function startCountdown() {
        // Get current time in UTC
        const now = new Date();

        // Create a new Date object for today's date at 12:00 noon ET (UTC-5)
        let targetTime = new Date("Jan 22 2025 13:00:00 UTC-5");
        //targetTime.setUTCHours(17, 0, 0, 0); // 12:00 noon ET is 17:00 UTC
        targetTime = targetTime - 5
        // If the target time has already passed today, set it for tomorrow
        if (now >= targetTime) {
            targetTime.setUTCDate(targetTime.getUTCDate() + 1);
        }

        // Function to update the countdown
        function updateCountdown() {
            const currentTime = new Date();
            const timeDifference = targetTime - currentTime;

            // Calculate time components
            const hours = Math.floor((timeDifference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((timeDifference % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeDifference % (1000 * 60)) / 1000);

            // Display the result
            document.getElementById('countdown').innerHTML = `${hours}h ${minutes}m ${seconds}s`;

            // If the countdown is over
            if (timeDifference < 0) {
                clearInterval(interval);
                document.getElementById('countdown').innerHTML = 'Time has passed!';
            }
        }

        // Update the countdown every second
        const interval = setInterval(updateCountdown, 1000);
        updateCountdown(); // Initial call to display the countdown immediately
    }

    // Start the countdown
    startCountdown();
});
