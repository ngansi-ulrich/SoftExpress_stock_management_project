/* ======================================================
   SoftExpress ERP Dashboard
   dashboard.js
====================================================== */

document.addEventListener("DOMContentLoaded", function () {

    initRevenueChart();
    initAgencyChart();

    animateCounters();

    loadCurrentDate();

});


/* ======================================================
   Counter Animation
====================================================== */

function animateCounters() {

    const counters = document.querySelectorAll("h2");

    counters.forEach(counter => {

        const value = counter.innerText;

        if (!value.match(/[0-9]/)) return;

        const finalValue = parseFloat(value.replace(/[^0-9.]/g, ""));

        if (isNaN(finalValue)) return;

        let current = 0;

        const increment = finalValue / 60;

        const timer = setInterval(() => {

            current += increment;

            if (current >= finalValue) {

                current = finalValue;

                clearInterval(timer);

            }

            if (value.includes("M")) {

                counter.innerText = current.toFixed(1) + "M FCFA";

            }

            else {

                counter.innerText = Math.floor(current);

            }

        }, 25);

    });

}


/* ======================================================
   Revenue Chart
====================================================== */

function initRevenueChart() {

    const canvas = document.getElementById("revenueChart");

    if (!canvas) return;

    new Chart(canvas, {

        type: 'line',

        data: {

            labels: [

                "Mon",

                "Tue",

                "Wed",

                "Thu",

                "Fri",

                "Sat",

                "Sun"

            ],

            datasets: [{

                label: "Revenue",

                data: [

                    2,

                    3,

                    4,

                    5,

                    6,

                    5,

                    7

                ],

                fill: true,

                borderColor: "#2563EB",

                backgroundColor: "rgba(37,99,235,.15)",

                tension: .4

            }]

        },

        options: {

            responsive: true,

            plugins: {

                legend: {

                    display: false

                }

            }

        }

    });

}


/* ======================================================
   Agency Chart
====================================================== */

function initAgencyChart() {

    const canvas = document.getElementById("agencyChart");

    if (!canvas) return;

    new Chart(canvas, {

        type: "doughnut",

        data: {

            labels: [

                "Douala",

                "Yaoundé",

                "Bafoussam"

            ],

            datasets: [{

                data: [

                    45,

                    35,

                    20

                ],

                backgroundColor: [

                    "#2563EB",

                    "#10B981",

                    "#F59E0B"

                ]

            }]

        },

        options: {

            plugins: {

                legend: {

                    position: "bottom"

                }

            }

        }

    });

}


/* ======================================================
   Today's Date
====================================================== */

function loadCurrentDate() {

    const target = document.getElementById("todayDate");

    if (!target) return;

    const today = new Date();

    target.innerHTML = today.toDateString();

}


/* ======================================================
   Auto Refresh
====================================================== */

setInterval(() => {

    console.log("Refreshing dashboard...");

    // Future AJAX request here

}, 300000);


/* ======================================================
   Notification Toast
====================================================== */

function showToast(message) {

    const toast = document.createElement("div");

    toast.className = "toast-box";

    toast.innerHTML = message;

    document.body.appendChild(toast);

    setTimeout(() => {

        toast.classList.add("show");

    }, 100);

    setTimeout(() => {

        toast.remove();

    }, 4000);

}


/* ======================================================
   Sidebar Toggle
====================================================== */

const toggle = document.getElementById("sidebarToggle");

if (toggle) {

    toggle.addEventListener("click", function () {

        document.querySelector(".sidebar").classList.toggle("show");

    });

}