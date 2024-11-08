let userId, currentYear, currentMonth;

userId = localStorage.getItem('userId') || 1;

window.initCalendar = function() {
    debugLog('initCalendar called');
    currentMonth = new Date().getMonth();
    currentYear = new Date().getFullYear();
    updateCalendar();
}

function addEventListeners() {
    document.getElementById('prevMonth').addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        updateCalendar();
    });

    document.getElementById('nextMonth').addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        updateCalendar();
    });
}

window.updateCalendar = function() {
    debugLog('updateCalendar called');
    document.getElementById('currentMonth').textContent = `${currentYear}, ${monthNames[currentMonth]}`;

    fetch(`/get_subscription_dates/${userId}/${currentYear}/${currentMonth + 1}`)
        .then(response => response.json())
        .then(data => {
            debugLog('Subscription dates received');
            renderCalendar(data);
        })
        .catch(error => debugLog('Error fetching subscription dates: ' + error));
}

window.renderCalendar = function(subscriptionDates) {
    debugLog('renderCalendar called');
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) {
        debugLog('Error: Calendar element not found');
        return;
    }
    calendarEl.innerHTML = '';

    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();

    debugLog(`Rendering calendar for ${currentMonth + 1}/${currentYear}`);
    debugLog(`Days in month: ${daysInMonth}, First day: ${firstDayOfMonth}`);

    // Создаем заголовки дней недели
    const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
    weekdays.forEach(day => {
        const dayEl = document.createElement('div');
        dayEl.classList.add('calendar-day', 'weekday');
        dayEl.textContent = day;
        calendarEl.appendChild(dayEl);
    });

    // Добавляем пустые ячейки для дней перед первым днем месяца
    for (let i = 0; i < (firstDayOfMonth + 6) % 7; i++) {
        calendarEl.appendChild(createDayElement(''));
    }

    // Добавляем дни месяца
    for (let day = 1; day <= daysInMonth; day++) {
        const dayEl = createDayElement(day);
        if (subscriptionDates && subscriptionDates[day]) {
            dayEl.classList.add('has-subscriptions');
            dayEl.addEventListener('click', () => showSubscriptions(day, subscriptionDates[day]));
        }
        calendarEl.appendChild(dayEl);
    }

    debugLog(`Calendar rendered with ${calendarEl.children.length} elements`);
}

function createDayElement(day) {
    const dayEl = document.createElement('div');
    dayEl.classList.add('calendar-day');
    dayEl.textContent = day;
    return dayEl;
}

function showSubscriptions(day, subscriptions) {
    const modal = document.getElementById('subscriptionModal');
    const modalDate = document.getElementById('modalDate');
    const modalSubscriptions = document.getElementById('modalSubscriptions');

    modalDate.textContent = `${day} ${getMonthName(currentMonth)} ${currentYear}`;
    modalSubscriptions.innerHTML = '';

    subscriptions.forEach(sub => {
        const subEl = document.createElement('div');
        subEl.classList.add('subscription-item');
        subEl.innerHTML = `
            <h4>${sub.service_name}</h4>
            <p>${sub.amount} ${sub.currency}</p>
        `;
        modalSubscriptions.appendChild(subEl);
    });

    modal.style.display = 'block';

    document.querySelector('.close').addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

function getMonthName(month) {
    const monthNames = ["января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"];
    return monthNames[month];
}

document.getElementById('prevMonth').addEventListener('click', () => {
    currentMonth--;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    }
    updateCalendar();
});

document.getElementById('nextMonth').addEventListener('click', () => {
    currentMonth++;
    if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    }
    updateCalendar();
});

document.querySelector('.close').addEventListener('click', () => {
    document.getElementById('subscriptionModal').style.display = 'none';
});

document.addEventListener('DOMContentLoaded', initCalendar);