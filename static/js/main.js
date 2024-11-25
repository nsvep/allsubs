// static/js/main.js

const tg = window.Telegram.WebApp;
let userId;
let services = [];
let categories = [];
let currentSlide = 1;
let isSaving = false;
let sortOrder = {
    amount: 'desc',
    next_payment: 'asc'
};
let currentDate = new Date();
let subscriptions = [];
let events = [];

// Кэширование DOM-элементов
const elements = {
    profileLink: document.getElementById('profileLink'),
    subscriptions: document.getElementById('subscriptions'),
    serviceSelect: document.getElementById('serviceSelect'),
    customService: document.getElementById('customService'),
    categorySelect: document.getElementById('categorySelect'),
    nextPaymentDate: document.getElementById('nextPaymentDate'),
    amount: document.getElementById('amount'),
    currency: document.getElementById('currency'),
    bank: document.getElementById('bank'),
    cardLast4: document.getElementById('cardLast4'),
    sendNotifications: document.getElementById('sendNotifications'),
    prevSlide: document.getElementById('prevSlide'),
    nextSlide: document.getElementById('nextSlide'),
    skipSlide: document.getElementById('skipSlide'),
    customServiceGroup: document.getElementById('customServiceGroup'),
    categoryGroup: document.getElementById('categoryGroup'),
    navCalendar: document.getElementById('navCalendar'),
    calendarView: document.getElementById('calendar-view'),
    currentMonth: document.getElementById('currentMonth'),
    calendarDays: document.getElementById('calendarDays'),
    prevMonth: document.getElementById('prevMonth'),
    nextMonth: document.getElementById('nextMonth'),
    eventList: document.getElementById('eventList'),

};

function closeSubscriptionForm() {
    toggleAddSubscriptionForm(false);
}
function animateLoadingScreen() {

    tg.expand();
    tg.HapticFeedback.impactOccurred('medium');
    const loadingScreen = document.getElementById('loading-screen');
    const circle = loadingScreen.querySelector('circle');

    anime({
        targets: circle,
        strokeDashoffset: [anime.setDashoffset, 0],
        easing: 'easeInOutSine',
        duration: 2000,
        delay: function(el, i) { return i * 150 },
        direction: 'alternate',
        loop: true
    });

    anime({
        targets: '.app-title',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 1500,
        easing: 'easeOutQuad'
    });

    anime({
        targets: '.loading-text',
        opacity: [0, 1],
        duration: 1500,
        delay: 500,
        easing: 'easeInOutQuad'
    });
}
// Инициализация приложения
async function init() {
    debugLog('Инициализация приложения начата');
    animateLoadingScreen();

    const telegramUser = tg.initDataUnsafe?.user;
    if (!telegramUser) {
        debugLog('Ошибка: данные пользователя Telegram не найдены');
        console.error('Telegram User data not found');
        setTimeout(hideLoadingScreen, 3000);
        return;
    }

    try {
        const response = await fetch('/get_user_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user: {
                    id: telegramUser.id,
                    first_name: telegramUser.first_name,
                    last_name: telegramUser.last_name,
                    username: telegramUser.username
                }
            }),
        });
        const data = await response.json();
        if (data.status === 'success') {
            userId = data.user_id;
            console.log('User ID set:', userId);
            debugLog(`Пользователь авторизован. ID: ${userId}`);
            showDebugOutputForAdmin(userId);

            try {
                const [servicesData, categoriesData] = await Promise.all([
                    fetchServices(),
                    fetchCategories()
                ]);

                services = servicesData;
                categories = categoriesData;

                // Используем updateSubscriptionsList вместо отдельных вызовов fetchSubscriptions и displaySubscriptions
                await updateSubscriptionsList();

                updateSelects(services, categories);
                initNavbar();
                debugLog('Вызвана функция initNavbar()');

                // Добавление обработчиков событий
                elements.serviceSelect.addEventListener('change', onServiceChange);
                elements.prevSlide.addEventListener('click', prevSlide);
                elements.nextSlide.addEventListener('click', nextSlide);
                elements.skipSlide.addEventListener('click', skipSlide);
                document.querySelectorAll('.close-button').forEach(button => {
                    button.addEventListener('click', closeSubscriptionForm);
                });
                elements.navCalendar.addEventListener('click', showCalendar);
                elements.prevMonth.addEventListener('click', () => {
                    currentDate.setMonth(currentDate.getMonth() - 1);
                    renderCalendar();
                });
                elements.nextMonth.addEventListener('click', () => {
                    currentDate.setMonth(currentDate.getMonth() + 1);
                    renderCalendar();
                });

                // Добавление обработчика для иконки профиля
                if (elements.profileLink) {
                    elements.profileLink.addEventListener('click', function(e) {
                        e.preventDefault();
                        showProfilePage();
                    });
                    elements.profileLink.style.display = 'block';
                }

                debugLog('Инициализация приложения завершена успешно');

                // Гарантированный вызов hideLoadingScreen через 5 секунд
                setTimeout(hideLoadingScreen, 3000);

            } catch (error) {
                debugLog(`Ошибка при загрузке данных: ${error.message}`);
                console.error('Error loading data:', error);
                setTimeout(hideLoadingScreen, 3000);
            }
        } else {
            debugLog('Ошибка при получении информации о пользователе');
            console.error('Error getting user info');
            setTimeout(hideLoadingScreen, 3000);
        }
    } catch (error) {
        debugLog(`Ошибка при инициализации: ${error.message}`);
        console.error('Error during initialization:', error);
        setTimeout(hideLoadingScreen, 3000);
    }
}

function initFormNavigation() {
    const prevSlideBtn = document.getElementById('prevSlide');
    const nextSlideBtn = document.getElementById('nextSlide');
    const skipSlideBtn = document.getElementById('skipSlide');

    prevSlideBtn.addEventListener('click', prevSlide);
    nextSlideBtn.addEventListener('click', nextSlide);
    skipSlideBtn.addEventListener('click', skipSlide);
}

// Получение списка сервисов
async function fetchServices() {
    debugLog('Начало загрузки списка сервисов');
    try {
        const response = await fetch('/get_services');
        const services = await response.json();
        debugLog(`Получено ${services.length} сервисов`);
        return services;
    } catch (error) {
        debugLog(`Ошибка при загрузке сервисов: ${error.message}`);
        console.error('Error fetching services:', error);
        throw error;
    }
}

// Получение списка категорий
async function fetchCategories() {
    debugLog('Начало загрузки списка категорий');
    try {
        const response = await fetch('/get_categories');
        const categories = await response.json();
        debugLog(`Получено ${categories.length} категорий`);
        return categories;
    } catch (error) {
        debugLog(`Ошибка при загрузке категорий: ${error.message}`);
        console.error('Error fetching categories:', error);
        throw error;
    }
}

// Обновление выпадающих списков
function updateSelects(services, categories) {
    updateSelect(elements.serviceSelect, services, 'id', 'name', true);
    updateSelect(elements.categorySelect, categories, 'id', 'name');
}

// Обработчик изменения выбора сервиса
function onServiceChange() {
    const isCustom = elements.serviceSelect.value === 'custom';
    elements.customServiceGroup.style.display = isCustom ? 'block' : 'none';
    elements.categoryGroup.style.display = isCustom ? 'block' : 'none';
}

// Получение списка подписок
async function fetchSubscriptions() {
    hideAllSections();
    elements.subscriptions.style.display = 'block';
    debugLog('Начало загрузки списка подписок');
    try {
        const response = await fetch(`/get_subscriptions/${userId}`);
        const subscriptions = await response.json();
        console.log("Received subscriptions:", subscriptions);
        debugLog(`Получено ${subscriptions.length} подписок`);
        return subscriptions;
    } catch (error) {
        debugLog(`Ошибка при загрузке подписок: ${error.message}`);
        console.error('Error fetching subscriptions:', error);
        throw error;
    }
}

// Отображение списка подписок
async function displaySubscriptions(subscriptions) {
    debugLog('Начало отображения подписок');
    elements.subscriptions.innerHTML = '';

    if (subscriptions.length === 0) {
        displayNoSubscriptions();
    } else {
        const subscriptionsList = document.createElement('div');
        subscriptionsList.className = 'subscriptions-list';

        for (const sub of subscriptions) {
            const subElement = await createSubscriptionElement(sub);
            subscriptionsList.appendChild(subElement);
        }

        elements.subscriptions.appendChild(subscriptionsList);
    }

}

function displayNoSubscriptions() {
    const noSubscriptionsElement = createNoSubscriptionsElement();
    elements.subscriptions.appendChild(noSubscriptionsElement);
    animateNoSubscriptions();
    debugLog('Отображено сообщение об отсутствии подписок с анимацией');
}

function createNoSubscriptionsElement() {
    const noSubscriptionsElement = document.createElement('div');
    noSubscriptionsElement.id = 'no-subscriptions';
    noSubscriptionsElement.className = 'no-subscriptions';
    noSubscriptionsElement.innerHTML = `
        <div class="animation-container">
            <i class="fas fa-music subscription-icon"></i>
            <i class="fas fa-film subscription-icon"></i>
            <i class="fas fa-cloud subscription-icon"></i>
            <i class="fas fa-newspaper subscription-icon"></i>
        </div>
        <h2>Нет активных подписок</h2>
        <p>Добавьте свою первую подписку, используя кнопку "+" в нижнем меню.</p>
    `;
    return noSubscriptionsElement;
}

async function displaySubscriptionsList(subscriptions) {
    const subscriptionsList = document.createElement('div');
    subscriptionsList.className = 'subscriptions-list';

    for (const sub of subscriptions) {
        const subElement = await createSubscriptionElement(sub);
        subscriptionsList.appendChild(subElement);
    }

    elements.subscriptions.appendChild(subscriptionsList);
}

function createSubscriptionElement(sub) {
    const subElement = document.createElement('div');
    subElement.className = 'subscription-item';
    subElement.setAttribute('data-id', sub.id);

    const nextPaymentDate = sub.next_payment_date ? new Date(sub.next_payment_date) : new Date(sub.start_date);
    const formattedDate = nextPaymentDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
    const amountClass = sub.amount > 1000 ? 'subscription-amount high' : 'subscription-amount';

    subElement.innerHTML = `
        <div class="subscription-header">
            <h3 class="subscription-service_name">${sub.service_name}</h3>
            <div class="subscription-actions">
                <button class="btn-more" onclick="showSubscriptionMenu(${sub.id})">⋮</button>
                <div id="menu-${sub.id}" class="subscription-menu" style="display: none;">
                    <button onclick="editSubscription(${sub.id})">Редактировать</button>
                    <button onclick="archiveSubscription(${sub.id})">Архивировать</button>
                    <button onclick="deleteSubscription(${sub.id})">Удалить</button>
                </div>
            </div>
        </div>
        ${createField('subscription-category_name', 'fas fa-tag', sub.category_name)}
        ${createField('subscription-next-payment', 'fas fa-calendar-alt', `Следующий платеж: ${formattedDate}`)}
        ${createField(amountClass, 'fas fa-money-bill-wave', `${sub.amount} ${sub.currency}`)}
        ${sub.discount ? createField('subscription-discount', 'fas fa-percent', `Скидка: ${sub.discount}%`) : ''}
        ${sub.bank ? createField('subscription-bank', 'fas fa-university', `Банк: ${sub.bank}`) : ''}
        ${sub.card_last_4 ? createField('subscription-card', 'fas fa-credit-card', `Карта: *${sub.card_last_4}`) : ''}
        ${sub.total_spent > 0 ? createField('subscription-total-spent', 'fas fa-chart-line', `Всего потрачено: ${sub.total_spent} ${sub.currency}`) : ''}
        ${sub.send_notifications ? createField('subscription-notifications', 'fas fa-bell', 'Уведомления включены') : ''}
    `;

    return subElement;
}

function createField(className, icon, content) {
    return `
        <p class="${className}">
            <i class="${icon}"></i>
            <span class="field-content">${content}</span>
        </p>
    `;
}

function showSubscriptionMenu(subscriptionId) {
    const menu = document.getElementById(`menu-${subscriptionId}`);
    const allMenus = document.querySelectorAll('.subscription-menu');

    // Закрываем все открытые меню
    allMenus.forEach(m => {
        if (m !== menu) {
            m.style.display = 'none';
        }
    });

    // Переключаем видимость текущего меню
    if (menu.style.display === 'block') {
        menu.style.display = 'none';
    } else {
        menu.style.display = 'block';

        // Проверяем положение меню относительно экрана
        const rect = menu.getBoundingClientRect();
        const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

        if (rect.bottom > viewportHeight) {
            menu.style.bottom = '100%';
            menu.style.top = 'auto';
        } else {
            menu.style.top = '100%';
            menu.style.bottom = 'auto';
        }
    }

    // Добавляем обработчик для закрытия меню при клике вне его
    document.addEventListener('click', function closeMenu(e) {
        if (!menu.contains(e.target) && e.target !== document.querySelector(`button[onclick="showSubscriptionMenu(${subscriptionId})"]`)) {
            menu.style.display = 'none';
            document.removeEventListener('click', closeMenu);
        }
    });
}

async function archiveSubscription(subscriptionId) {
    if (confirm('Вы уверены, что хотите архивировать эту подписку?')) {
        try {
            const response = await fetch(`/archive_subscription/${subscriptionId}`, {method: 'POST'});
            if (response.ok) {
                await updateSubscriptionsList();
                tg.showPopup({message: 'Подписка архивирована'});
            } else {
                throw new Error('Failed to archive subscription');
            }
        } catch (error) {
            console.error('Error archiving subscription:', error);
            tg.showPopup({message: 'Ошибка при архивировании подписки'});
        }
    }
}
// Сохранение подписки
async function saveSubscription(subscriptionId = null) {
    if (isSaving) return; // Если уже идет сохранение, просто выходим
    isSaving = true; // Устанавливаем флаг, что началось сохранение
    debugLog('Начало сохранения подписки');

    // Проверяем все слайды перед сохранением
    for (let i = 1; i <= 3; i++) {
        if (!validateSlide(i)) {
            isSaving = false;
            return;
        }
    }

    const isCustomService = elements.serviceSelect.value === 'custom';

    const subscriptionData = {
        user_id: userId,
        service_name: isCustomService ? elements.customService.value : elements.serviceSelect.value,
        next_payment_date: elements.nextPaymentDate.value,
        amount: parseFloat(elements.amount.value),
        currency: elements.currency.value,
        bank: elements.bank.value,
        card_last_4: elements.cardLast4.value,
        send_notifications: elements.sendNotifications.checked
    };

    if (isCustomService) {
        subscriptionData.category_id = elements.categorySelect.value;
    }

    console.log('Sending subscription data:', subscriptionData);

    try {
        const url = subscriptionId ? `/update_subscription/${subscriptionId}` : '/add_subscription';
        debugLog(`Отправка запроса на ${url}`);
        const response = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(subscriptionData)
        });

        const result = await response.json();

        if (response.ok) {
            tg.HapticFeedback.impactOccurred('medium');
            debugLog('Подписка успешно сохранена');
            toggleAddSubscriptionForm(false);
            await updateSubscriptionsList();
            tg.showPopup({message: subscriptionId ? 'Подписка обновлена' : 'Подписка добавлена'});
        } else {
            throw new Error(result.error || 'Неизвестная ошибка при сохранении подписки');
        }
    } catch (error) {
        console.error('Error saving subscription:', error);
        tg.showPopup({message: `Ошибка при сохранении подписки: ${error.message}`});
    } finally {
        isSaving = false;
    }
}

// Удаление подписки
async function deleteSubscription(subscriptionId) {
    debugLog(`Начало удаления подписки с ID: ${subscriptionId}`);
    if (confirm('Вы уверены, что хотите удалить эту подписку?')) {
        try {
            const response = await fetch(`/delete_subscription/${subscriptionId}`, {method: 'DELETE'});
            if (response.ok) {
                debugLog('Подписка успешно удалена');
                await updateSubscriptionsList();
                tg.showPopup({message: 'Подписка удалена'});
            } else {
                debugLog('Ошибка при удалении подписки');
                throw new Error('Failed to delete subscription');
            }
        } catch (error) {
            debugLog(`Ошибка при удалении подписки: ${error.message}`);
            console.error('Error deleting subscription:', error);
            tg.showPopup({message: 'Ошибка при удалении подписки'});
        }
    }
}

// Редактирование подписки

async function updateSubscriptionsList() {
    try {
        const subscriptions = await fetchSubscriptions();
        await displaySubscriptions(subscriptions);
    } catch (error) {
        debugLog(`Ошибка при обновлении списка подписок: ${error.message}`);
        console.error('Error updating subscriptions list:', error);
    }
}

function toggleAddSubscriptionForm(show) {
    const addSubscriptionForm = document.getElementById('add-subscription-form');
    const subscriptionsList = document.getElementById('subscriptions');

    if (show) {
        hideAllSections();
        addSubscriptionForm.style.display = 'block';
        subscriptionsList.style.display = 'none';
        resetForm();
        currentSlide = 1;
        showSlide(currentSlide);
        updateProgressBar();
        updateNavigationButtons();
        toggleNavbar(false);

        // Скрываем иконку профиля
        if (elements.profileLink) {
            elements.profileLink.style.display = 'none';
        }

        // Скрываем кнопку "Назад к подпискам", если она есть
        const backButton = document.querySelector('.back-button');
        if (backButton) {
            backButton.style.display = 'none';
        }

        // Анимация открытия формы
        anime({
            targets: addSubscriptionForm,
            translateY: ['100%', '0%'],
            duration: 500,
            easing: 'easeOutExpo'
        });
    } else {
        // Анимация закрытия формы
        anime({
            targets: addSubscriptionForm,
            translateY: ['0%', '100%'],
            duration: 500,
            easing: 'easeInExpo',
            complete: function() {
                addSubscriptionForm.style.display = 'none';
                subscriptionsList.style.display = 'block';
                resetForm();
                toggleNavbar(true);

                // Показываем иконку профиля
                if (elements.profileLink) {
                    elements.profileLink.style.display = 'block';
                }

                // Показываем кнопку "Назад к подпискам", если мы на странице профиля
                const profileSection = document.getElementById('profile-section');
                if (profileSection && profileSection.style.display !== 'none') {
                    const backButton = document.querySelector('.back-button');
                    if (backButton) {
                        backButton.style.display = 'block';
                    }
                }

                // Активируем пункт "Подписки" в нижнем navbar
                const navItems = document.querySelectorAll('.nav-item');
                const subscriptionsNavItem = document.getElementById('navSubscriptions');

                navItems.forEach(item => item.classList.remove('active'));
                subscriptionsNavItem.classList.add('active');

                // Перемещаем индикатор
                setIndicatorPosition(subscriptionsNavItem);
            }
        });
    }
}

// Сброс формы
function resetForm() {
    elements.serviceSelect.value = '';
    elements.customService.value = '';
    elements.categorySelect.value = '';
    elements.nextPaymentDate.value = '';
    elements.amount.value = '';
    elements.currency.value = 'RUB';
    elements.bank.value = '';
    elements.cardLast4.value = '';
    elements.sendNotifications.checked = false;
    onServiceChange();
    currentSlide = 1;
    showSlide(currentSlide);
    updateNavigationButtons();
    updateProgressBar();
}

// Показать слайд
function showSlide(slideNumber) {
    const slides = document.querySelectorAll('.subscription-slide');
    slides.forEach((slide, index) => {
        slide.style.display = index + 1 === slideNumber ? 'block' : 'none';
    });
}

// Обновление кнопок навигации
function updateNavigationButtons() {
    const prevSlideBtn = document.getElementById('prevSlide');
    const nextSlideBtn = document.getElementById('nextSlide');
    const skipSlideBtn = document.getElementById('skipSlide');

    prevSlideBtn.style.display = currentSlide > 1 ? 'inline-block' : 'none';

    if (currentSlide === 3) {
        nextSlideBtn.textContent = 'Сохранить';
        skipSlideBtn.style.display = 'inline-block';
    } else {
        nextSlideBtn.textContent = 'Далее';
        skipSlideBtn.style.display = 'none';
    }
}

// Предыдущий слайд
function prevSlide() {
    if (currentSlide > 1) {
        showSlide(--currentSlide);
        updateNavigationButtons();
        updateProgressBar();
    }
}

// Следующий слайд
function nextSlide() {
    if (validateSlide(currentSlide)) {
        if (currentSlide < 3) {
            showSlide(++currentSlide);
            updateNavigationButtons();
            updateProgressBar();
        } else {
            saveSubscription();
        }
    }
}

// Валидация слайда
function isValidDate(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const fiveYearsFromNow = new Date(today);
    fiveYearsFromNow.setFullYear(today.getFullYear() + 5);

    return date >= today && date <= fiveYearsFromNow;
}

function isValidAmount(amountString) {
    const amount = parseFloat(amountString);
    return !isNaN(amount) && amount > 0;
}

function isValidString(str, minLength = 1, maxLength = 100) {
    return str && typeof str === 'string' && str.length >= minLength && str.length <= maxLength;
}

function isValidSelect(value) {
    return value && value !== 'default';
}

function isValidCardLast4(cardLast4) {
    return /^\d{4}$/.test(cardLast4);
}

function validateSlide(slideNumber) {
    switch (slideNumber) {
        case 1:
            if (!isValidSelect(elements.serviceSelect.value)) {
                if (elements.serviceSelect.value === 'custom' && !isValidString(elements.customService.value, 2, 50)) {
                    tg.showPopup({ message: 'Название сервиса должно содержать от 2 до 50 символов' });
                    return false;
                }
                tg.showPopup({ message: 'Пожалуйста, выберите сервис или введите название кастомного сервиса' });
                return false;
            }
            if (elements.serviceSelect.value === 'custom' && !isValidSelect(elements.categorySelect.value)) {
                tg.showPopup({ message: 'Пожалуйста, выберите категорию для кастомного сервиса' });
                return false;
            }
            return true;

        case 2:
            if (!isValidDate(elements.nextPaymentDate.value)) {
                tg.showPopup({ message: 'Пожалуйста, укажите корректную дату следующего платежа' });
                return false;
            }
            if (!isValidAmount(elements.amount.value)) {
                tg.showPopup({ message: 'Пожалуйста, укажите корректную сумму платежа' });
                return false;
            }
            if (!isValidSelect(elements.currency.value)) {
                tg.showPopup({ message: 'Пожалуйста, выберите валюту' });
                return false;
            }
            return true;

        case 3:
            // Все поля на третьем слайде необязательны, но если они заполнены, то должны быть валидными
            if (elements.bank.value && !isValidString(elements.bank.value, 2, 50)) {
                tg.showPopup({ message: 'Название банка должно содержать от 2 до 50 символов' });
                return false;
            }
            if (elements.cardLast4.value && !isValidCardLast4(elements.cardLast4.value)) {
                tg.showPopup({ message: 'Последние 4 цифры карты должны содержать 4 цифры' });
                return false;
            }
            return true;

        default:
            console.error('Неизвестный номер слайда:', slideNumber);
            return false;
    }
}

// Пропустить слайд
function skipSlide() {
    if (currentSlide === 3) {
        // Очистим поля банка и номера карты
        document.getElementById('bank').value = '';
        document.getElementById('cardLast4').value = '';
        document.getElementById('sendNotifications').checked = false;

        // Сохраняем подписку
        saveSubscription();
    }
}

function setIndicatorPosition(item) {
    const navIndicator = document.querySelector('.nav-indicator');
    const itemRect = item.getBoundingClientRect();
    const navbarRect = item.closest('.bottom-navbar').getBoundingClientRect();

    anime({
        targets: navIndicator,
        width: `${itemRect.width}px`,
        left: `${itemRect.left - navbarRect.left}px`,
        easing: 'easeOutElastic(1, .5)',
        duration: 600
    });
}
// Инициализация нижней навигации
function initNavbar() {
    debugLog('Инициализация навигационной панели');

    const navItems = document.querySelectorAll('.nav-item');
    const navIndicator = document.querySelector('.nav-indicator');
    const navActions = {
        'navSubscriptions': async () => {
            debugLog('Нажата кнопка подписок');
            try {
                await updateSubscriptionsList();
                // Здесь можно добавить дополнительную логику, если нужно
            } catch (error) {
                console.error('Error updating subscriptions list:', error);
                debugLog(`Ошибка при обновлении списка подписок: ${error.message}`);
            }
        },
        'navAddSubscription': () => {
            debugLog('Нажата кнопка добавления подписки');
            hideAllSections();
            toggleAddSubscriptionForm(true);
        },
        'navCalendar': () => {
            debugLog('Нажата кнопка календаря');
            showCalendar();
        }
    };

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            setIndicatorPosition(item);
            hideAllSections(); // Скрываем все секции перед показом новой
            const action = navActions[item.id];
            if (action) {
                action();
            }
        });
    });

    // Устанавливаем начальную позицию индикатора
    const activeItem = document.querySelector('.nav-item.active');
    if (activeItem) {
        setIndicatorPosition(activeItem);
    }

    // Обработка изменения размера окна
    window.addEventListener('resize', () => {
        const currentActiveItem = document.querySelector('.nav-item.active');
        if (currentActiveItem) {
            setIndicatorPosition(currentActiveItem);
        }
    });

    debugLog('Инициализация навигационной панели завершена');
}
// Обновление выпадающего списка
function updateSelect(selectElement, options, valueKey, textKey, addCustomOption = false) {
    selectElement.innerHTML = '';
    if (addCustomOption) {
        const customOption = document.createElement('option');
        customOption.value = 'custom';
        customOption.textContent = 'Другое (ввести вручную)';
        selectElement.appendChild(customOption);
    }
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option[valueKey];
        optionElement.textContent = option[textKey];
        selectElement.appendChild(optionElement);
    });
}

function debugLog(message) {
    const debugOutput = document.getElementById('debug-output');
    const debugContent = document.getElementById('debug-content');
    if (debugOutput && debugOutput.style.display !== 'none' && debugContent) {
        const logEntry = document.createElement('p');
        logEntry.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${message}`;
        debugContent.appendChild(logEntry);
        debugContent.scrollTop = debugContent.scrollHeight;
    }
}

function showDebugOutputForAdmin(userId) {
    const debugOutput = document.getElementById('debug-output');
    if (debugOutput && userId === 1) {
        debugOutput.style.display = 'block';
        debugLog('Debug output shown for admin');
        initDebugWindow();
        initDebugSendButton();  // Добавим эту строку
    }
}

function clearDebugOutput() {
    const debugContent = document.getElementById('debug-content');
    if (debugContent) {
        debugContent.innerHTML = '';
    }
}

function toggleNavbar(show) {
    const navbar = document.querySelector('.bottom-navbar');
    if (show) {
        navbar.style.display = 'flex';
        // Показываем иконку профиля
        if (elements.profileLink) {
            elements.profileLink.style.display = 'block';
        }
    } else {
        navbar.style.display = 'none';

        // Добавьте кнопку "Назад" при скрытии навбара
        const backButton = document.createElement('button');
        backButton.textContent = 'Назад к подпискам';
        backButton.classList.add('back-button');
        backButton.style.opacity = '0';  // Начальная прозрачность для анимации
        backButton.addEventListener('click', () => {
            anime({
                targets: '#profile-section',
                opacity: 0,
                translateY: 20,
                duration: 500,
                easing: 'easeInCubic',
                complete: function() {
                    document.getElementById('profile-section').style.display = 'none';
                    elements.subscriptions.style.display = 'block';
                    animateSubscriptionsReturn();  // Добавляем анимацию возврата
                    toggleNavbar(true);
                    backButton.remove();
                }
            });
        });
        document.querySelector('main').prepend(backButton);

        // Анимация появления кнопки "Назад"
        anime({
            targets: backButton,
            opacity: [0, 1],
            translateX: [-20, 0],
            duration: 500,
            easing: 'easeOutCubic'
        });
    }
}

async function editSubscription(subscriptionId) {
    debugLog(`Начало редактирования подписки с ID: ${subscriptionId}`);
    const subscriptionItem = document.querySelector(`.subscription-item[data-id="${subscriptionId}"]`);
    if (!subscriptionItem) {
        debugLog(`Подписка с ID ${subscriptionId} не найдена`);
        return;
    }

    // Скрываем меню подписки
    const subscriptionMenu = subscriptionItem.querySelector('.subscription-menu');
    if (subscriptionMenu) {
        subscriptionMenu.style.display = 'none';
    }

    subscriptionItem.classList.add('editing');

    const currentServiceName = subscriptionItem.querySelector('.subscription-service_name').textContent;
    const currentCategoryName = subscriptionItem.querySelector('.subscription-category_name .field-content').textContent;
    const currentAmount = subscriptionItem.querySelector('.subscription-amount .field-content').textContent.split(' ')[0];
    const currentCurrency = subscriptionItem.querySelector('.subscription-amount .field-content').textContent.split(' ')[1];

    debugLog(`Текущие данные подписки: Сервис: ${currentServiceName}, Категория: ${currentCategoryName}, Сумма: ${currentAmount}, Валюта: ${currentCurrency}`);

    const editForm = document.createElement('form');
    editForm.className = 'edit-form';
    editForm.innerHTML = `
        <div class="form-group">
            <label for="edit-service">Сервис</label>
            <select id="edit-service" required>
                <option value="">Выберите сервис</option>
                ${services.map(service => `<option value="${service.name}" ${service.name === currentServiceName ? 'selected' : ''}>${service.name}</option>`).join('')}
                <option value="custom">Другой (свой вариант)</option>
            </select>
            <input type="text" id="edit-custom-service" style="display: none;" placeholder="Введите название сервиса" value="${currentServiceName}">
        </div>
        <div class="form-group">
            <label for="edit-category">Категория</label>
            <select id="edit-category" disabled>
                ${categories.map(category => `<option value="${category.name}" ${category.name === currentCategoryName ? 'selected' : ''}>${category.name}</option>`).join('')}
            </select>
        </div>
        <div class="form-group">
            <label for="edit-amount">Сумма</label>
            <input type="number" id="edit-amount" value="${currentAmount}" required>
        </div>
        <div class="form-group">
            <label for="edit-currency">Валюта</label>
            <select id="edit-currency" required>
                <option value="RUB" ${currentCurrency === 'RUB' ? 'selected' : ''}>RUB</option>
                <option value="USD" ${currentCurrency === 'USD' ? 'selected' : ''}>USD</option>
                <option value="EUR" ${currentCurrency === 'EUR' ? 'selected' : ''}>EUR</option>
            </select>
        </div>
        <div class="edit-actions">
            <button type="submit" class="btn-save">Сохранить</button>
            <button type="button" class="btn-cancel">Отмена</button>
        </div>
    `;

    const editServiceSelect = editForm.querySelector('#edit-service');
    const editCategorySelect = editForm.querySelector('#edit-category');
    const editCustomServiceInput = editForm.querySelector('#edit-custom-service');

    // Устанавливаем начальное состояние
    if (!services.some(service => service.name === currentServiceName)) {
        debugLog(`Установка пользовательского сервиса: ${currentServiceName}`);
        editServiceSelect.value = 'custom';
        editCustomServiceInput.style.display = 'block';
        editCategorySelect.disabled = false;
    }

    editServiceSelect.addEventListener('change', function() {
        debugLog(`Изменение выбора сервиса: ${this.value}`);
        const selectedService = services.find(service => service.name === this.value);
        if (selectedService) {
            editCategorySelect.value = categories.find(category => category.id === selectedService.category_id).name;
            editCategorySelect.disabled = true;
            editCustomServiceInput.style.display = 'none';
        } else if (this.value === 'custom') {
            editCategorySelect.disabled = false;
            editCustomServiceInput.style.display = 'block';
        } else {
            editCategorySelect.disabled = true;
            editCustomServiceInput.style.display = 'none';
        }
    });

    subscriptionItem.appendChild(editForm);

    // Добавляем анимацию появления формы
    animateEditForm(editForm);

    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const updatedData = {
            service_name: editServiceSelect.value === 'custom' ? editCustomServiceInput.value : editServiceSelect.value,
            category_name: editCategorySelect.value,
            amount: parseFloat(editForm.querySelector('#edit-amount').value),
            currency: editForm.querySelector('#edit-currency').value
        };

        debugLog(`Отправка обновленных данных: ${JSON.stringify(updatedData)}`);
        console.log('Updating subscription with data:', updatedData);
        console.log('Selected service:', editServiceSelect.value);
        console.log('Custom service input:', editCustomServiceInput.value);

        try {
            const response = await fetch(`/update_subscription/${subscriptionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updatedData),
            });

            if (response.ok) {
                const result = await response.json();
                debugLog(`Ответ сервера: ${JSON.stringify(result)}`);
                console.log('Server response:', result);
                await updateSubscriptionsList();
                tg.showPopup({
                    title: 'Успех',
                    message: 'Подписка успешно обновлена',
                    buttons: [{ type: 'close' }]
                });
            } else {
                throw new Error('Failed to update subscription');
            }
        } catch (error) {
            debugLog(`Ошибка при обновлении подписки: ${error.message}`);
            console.error('Error updating subscription:', error);
            tg.showPopup({
                title: 'Ошибка',
                message: 'Не удалось обновить подписку. Пожалуйста, попробуйте еще раз.',
                buttons: [{ type: 'close' }]
            });
        } finally {
            // Возвращаем видимость меню подписки и удаляем форму редактирования
            if (subscriptionMenu) {
                subscriptionMenu.style.display = '';
            }
            subscriptionItem.classList.remove('editing');
            editForm.remove();
        }
    });

    editForm.querySelector('.btn-cancel').addEventListener('click', () => {
        debugLog('Отмена редактирования подписки');
        // Возвращаем видимость меню подписки и удаляем форму редактирования
        if (subscriptionMenu) {
            subscriptionMenu.style.display = '';
        }
        subscriptionItem.classList.remove('editing');
        editForm.remove();
    });
}

async function loadServicesAndCategories() {
    try {
        const servicesResponse = await fetch('/get_services');
        services = await servicesResponse.json();

        const categoriesResponse = await fetch('/get_categories');
        categories = await categoriesResponse.json();
    } catch (error) {
        console.error('Error loading services and categories:', error);
    }
}

function updateProgressBar() {
    const progressBar = document.getElementById('subscriptionProgress');
    const progress = (currentSlide / 3) * 100;
    progressBar.style.width = `${progress}%`;
}

function animateNoSubscriptions() {
    anime({
        targets: '.subscription-icon',
        translateY: [-50, 0],
        opacity: [0, 1],
        scale: [0.5, 1],
        delay: anime.stagger(200),
        duration: 1000,
        easing: 'spring(1, 80, 10, 0)',
        loop: true,
        direction: 'alternate'
    });
}

function animateEditForm(editForm) {
    anime({
        targets: editForm,
        opacity: [0, 1],
        translateY: [-20, 0],
        duration: 500,
        easing: 'easeOutCubic'
    });
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        anime({
            targets: loadingScreen,
            opacity: [1, 0],
            duration: 1200,
            easing: 'easeOutQuad',
            complete: function() {
                loadingScreen.style.display = 'none';
                console.log('Loading screen hidden');
                debugLog('Загрузочный экран скрыт');
            }
        });
    } else {
        console.error('Loading screen element not found');
        debugLog('Элемент загрузочного экрана не найден');
    }
}

function showProfilePage() {
    // Скрываем все секции
    hideAllSections();

    // Показываем страницу профиля
    let profileSection = document.getElementById('profile-section');
    if (!profileSection) {
        profileSection = document.createElement('section');
        profileSection.id = 'profile-section';
        profileSection.innerHTML = '<h2>Профиль пользователя</h2><p>Здесь будет информация о профиле.</p>';
        document.querySelector('main').appendChild(profileSection);
    }
    profileSection.style.display = 'block';
    profileSection.style.opacity = '0';  // Начальная прозрачность для анимации

    // Скрываем иконку профиля
    if (elements.profileLink) {
        elements.profileLink.style.display = 'none';
    }

    // Скрываем нижнюю навигацию
    toggleNavbar(false);

    // Анимация появления профиля
    anime({
        targets: profileSection,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800,
        easing: 'easeOutCubic'
    });

    // Добавляем кнопку "Назад"
    addBackButton();

    // Убедимся, что обработчик события добавлен
    const backButton = document.querySelector('.back-button');
    if (backButton) {
        backButton.removeEventListener('click', handleBackButton); // Удаляем старый обработчик, если он есть
        backButton.addEventListener('click', handleBackButton); // Добавляем новый обработчик
    }
}

function animateSubscriptionsReturn() {
    anime({
        targets: elements.subscriptions,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800,
        easing: 'easeOutCubic'
    });
}

async function showCalendar(event) {
    if (event) event.preventDefault();
    hideAllSections();
    elements.calendarView.style.display = 'block';
    debugLog('Начало отображения календаря');
    await loadEvents(); // Загружаем события перед рендерингом календаря
    renderCalendar();
    toggleNavbar(true);
    debugLog('Завершение отображения календаря');
}

function hideAllSections() {
    const sections = document.querySelectorAll('main > section');
    sections.forEach(section => section.style.display = 'none');

    // Явно скрываем календарь и профиль
    if (elements.calendarView) {
        elements.calendarView.style.display = 'none';
    }
    const profileSection = document.getElementById('profile-section');
    if (profileSection) {
        profileSection.style.display = 'none';
    }

    // Скрываем кнопку "Назад"
    const backButton = document.querySelector('.back-button');
    if (backButton) {
        backButton.style.display = 'none';
    }
}

function renderCalendar() {
    const monthNames = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];

    elements.currentMonth.textContent = `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`;

    elements.calendarDays.innerHTML = '';

    const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

    // Добавляем пустые ячейки для дней до начала месяца
    for (let i = 0; i < firstDay.getDay(); i++) {
        const emptyDay = document.createElement('div');
        emptyDay.classList.add('calendar-day', 'empty');
        elements.calendarDays.appendChild(emptyDay);
    }

    const today = new Date();

    for (let i = 1; i <= lastDay.getDate(); i++) {
        const dayElement = document.createElement('div');
        dayElement.textContent = i;
        dayElement.classList.add('calendar-day');

        const currentDateString = `${currentDate.getFullYear()}-${(currentDate.getMonth() + 1).toString().padStart(2, '0')}-${i.toString().padStart(2, '0')}`;

        const isToday = i === today.getDate() &&
                        currentDate.getMonth() === today.getMonth() &&
                        currentDate.getFullYear() === today.getFullYear();

        if (isToday) {
            dayElement.classList.add('today');
        }

        if (hasEvent(currentDateString)) {
            dayElement.classList.add('has-event');
        }

        if (isPastEvent(currentDateString)) {
            dayElement.classList.add('past-event');
        }

        if (isToday && hasEvent(currentDateString)) {
            dayElement.classList.add('today-has-event');
        }

        dayElement.addEventListener('click', () => showEvents(currentDateString));
        elements.calendarDays.appendChild(dayElement);
    }
}

function hasEvent(dateString) {
    return events.some(event => event.date === dateString);
}

function isPastEvent(dateString) {
    return events.some(event => event.date === dateString && event.isPast);
}

function showEvents(dateString) {
    const eventList = document.getElementById('eventList');
    eventList.innerHTML = '';

    const dayEvents = events.filter(event => event.date === dateString);

    if (dayEvents.length === 0) {
        eventList.innerHTML = '<p>На этот день события не запланированы.</p>';
        return;
    }

    dayEvents.forEach(event => {
        const eventItem = document.createElement('div');
        eventItem.classList.add('event-item');
        if (event.isPast) {
            eventItem.classList.add('past-event');
        }
        eventItem.innerHTML = `
            <h3>${event.service}</h3>
            <p>Сумма: ${event.amount} ${event.currency}</p>
            <p>${event.isPast ? 'Прошедший платеж' : 'Предстоящий платеж'}</p>
        `;
        eventList.appendChild(eventItem);
    });
}

function addBackButton() {
    let backButton = document.querySelector('.back-button');
    if (!backButton) {
        backButton = document.createElement('button');
        backButton.textContent = 'Назад к подпискам';
        backButton.classList.add('back-button');
        document.querySelector('main').prepend(backButton);
    }

    backButton.style.display = 'block';
    backButton.addEventListener('click', handleBackButton);
}

function handleBackButton() {
    const profileSection = document.getElementById('profile-section');
    anime({
        targets: profileSection,
        opacity: 0,
        translateY: 20,
        duration: 500,
        easing: 'easeInCubic',
        complete: async function() {
            profileSection.style.display = 'none';
            try {
                await updateSubscriptionsList();
            } catch (error) {
                console.error('Error updating subscriptions:', error);
                debugLog(`Ошибка при обновлении подписок: ${error.message}`);
            }
            toggleNavbar(true);
            document.querySelector('.back-button').style.display = 'none';
        }
    });
}

async function loadUserSubscriptions() {
    debugLog('Начало загрузки подписок пользователя');
    try {
        debugLog(`Отправка запроса на /api/calendar-events?user_id=${userId}`);
        const response = await fetch(`/api/calendar-events?user_id=${userId}`);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
        const data = await response.json();
        subscriptions = data;
        debugLog(`Успешно загружено ${subscriptions.length} подписок`);
        debugLog('Данные подписок:', JSON.stringify(subscriptions));
    } catch (error) {
        debugLog(`Ошибка при загрузке подписок: ${error.message}`);
        console.error('Error loading subscriptions:', error);
    }
    debugLog('Завершение загрузки подписок пользователя');
}

function initDebugWindow() {
    const debugWindow = document.getElementById('debug-output');
    const toggleButton = document.getElementById('toggle-debug');
    const clearButton = document.getElementById('clear-debug');
    const debugContent = document.getElementById('debug-content');
    const sendDebugButton = document.getElementById('send-debug');

    // Сворачивание/разворачивание окна
    toggleButton.addEventListener('click', () => {
        debugContent.style.display = debugContent.style.display === 'none' ? 'block' : 'none';
        toggleButton.textContent = debugContent.style.display === 'none' ? '+' : '_';
    });

    // Очистка содержимого
    clearButton.addEventListener('click', clearDebugOutput);
}

async function sendDebugLog() {
    debugLog('sendDebugLog function called');
    const debugContent = document.getElementById('debug-content').innerText;
    debugLog('Preparing to send debug content');
    try {
        debugLog('Sending POST request to /api/send_debug_log');
        const response = await fetch('/api/send_debug_log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                debug_log: debugContent
            }),
        });
        debugLog(`Response received: status ${response.status}`);
        const data = await response.json();
        debugLog(`Response data: ${JSON.stringify(data)}`);
        if (data.status === 'success') {
            debugLog('Debug log sent successfully');
            alert('Debug log sent successfully');
        } else {
            debugLog(`Failed to send debug log: ${data.error || 'Unknown error'}`);
            alert('Failed to send debug log: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        debugLog(`Error sending debug log: ${error.message}`);
        console.error('Error sending debug log:', error);
        alert('Error sending debug log: ' + error.message);
    }
}

function initDebugSendButton() {
    debugLog('Initializing debug send button');
    const sendDebugButton = document.getElementById('send-debug');
    if (sendDebugButton) {
        debugLog('Debug send button found, adding click event listener');
        sendDebugButton.addEventListener('click', sendDebugLog);
    } else {
        debugLog('Debug send button not found');
    }
}

async function loadEvents() {
    try {
        const response = await fetch(`/api/calendar-events?user_id=${userId}`);
        if (!response.ok) {
            throw new Error('Failed to load events');
        }
        events = await response.json();
    } catch (error) {
        console.error('Error loading events:', error);
    }
}


// Инициализация приложения при загрузке
document.addEventListener('DOMContentLoaded', () => {
    init().catch(error => console.error('Error in init:', error));
});