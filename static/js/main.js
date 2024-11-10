// static/js/main.js

const tg = window.Telegram.WebApp;
let userId;
let services = [];
let categories = [];
let currentSlide = 1;
let isSaving = false;

// Кэширование DOM-элементов
const elements = {
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
    categoryGroup: document.getElementById('categoryGroup')
};

function closeSubscriptionForm() {
    toggleAddSubscriptionForm(false);
}
function animateLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    const circle = loadingScreen.querySelector('circle');

    anime({
        targets: circle,
        strokeDashoffset: [anime.setDashoffset, 0],
        easing: 'easeInOutSine',
        duration: 3000,
        delay: function(el, i) { return i * 250 },
        direction: 'alternate',
        loop: true
    });

    anime({
        targets: '.app-title',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 2000,
        easing: 'easeOutQuad'
    });

    anime({
        targets: '.loading-text',
        opacity: [0, 1],
        duration: 2000,
        delay: 1000,
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
        setTimeout(hideLoadingScreen, 5000);
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
                const [servicesData, categoriesData, subscriptionsData] = await Promise.all([
                    fetchServices(),
                    fetchCategories(),
                    fetchSubscriptions()
                ]);

                services = servicesData;
                categories = categoriesData;
                await updateSubscriptionsList();

                updateSelects(services, categories);
                initNavbar();
                debugLog('Вызвана функция initNavbar()');

                elements.serviceSelect.addEventListener('change', onServiceChange);
                elements.prevSlide.addEventListener('click', prevSlide);
                elements.nextSlide.addEventListener('click', nextSlide);
                elements.skipSlide.addEventListener('click', skipSlide);
                document.querySelectorAll('.close-button').forEach(button => {
                    button.addEventListener('click', closeSubscriptionForm);
                });
                debugLog('Инициализация приложения завершена успешно');

                // Гарантированный вызов hideLoadingScreen через 5 секунд
                setTimeout(hideLoadingScreen, 5000);
            } catch (error) {
                debugLog(`Ошибка при загрузке данных: ${error.message}`);
                console.error('Error loading data:', error);
                setTimeout(hideLoadingScreen, 5000);
            }
        } else {
            debugLog('Ошибка при получении информации о пользователе');
            console.error('Error getting user info');
            setTimeout(hideLoadingScreen, 5000);
        }
    } catch (error) {
        debugLog(`Ошибка при инициализации: ${error.message}`);
        console.error('Error during initialization:', error);
        setTimeout(hideLoadingScreen, 5000);
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
function displaySubscriptions(subscriptions) {
    debugLog('Начало отображения подписок');
    elements.subscriptions.innerHTML = '';

        if (subscriptions.length === 0) {
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
        elements.subscriptions.appendChild(noSubscriptionsElement);
        animateNoSubscriptions();
        debugLog('Отображено сообщение об отсутствии подписок с анимацией');
    } else {
        const subscriptionsList = document.createElement('div');
        subscriptionsList.className = 'subscriptions-list';

        subscriptions.forEach(sub => {
            const subElement = document.createElement('div');
            subElement.className = 'subscription-item';
            subElement.setAttribute('data-id', sub.id);

            // Форматируем дату следующего платежа
            const nextPaymentDate = new Date(sub.start_date);
            const formattedDate = nextPaymentDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });

            // Определяем класс для суммы (для возможной цветовой индикации)
            const amountClass = sub.amount > 1000 ? 'subscription-amount high' : 'subscription-amount';

            // Создаем элементы для каждого поля подписки
            const createField = (className, icon, content) => `
                <p class="${className}">
                    <i class="${icon}"></i>
                    <span class="field-content">${content}</span>
                </p>
            `;

            // Создаем базовую структуру подписки
            let subscriptionHTML = `
                <div class="subscription-header">
                    <h3 class="subscription-service_name">${sub.service_name}</h3>
                    <button class="btn-more" onclick="showSubscriptionMenu(${sub.id})">⋮</button>
                </div>
                ${createField('subscription-category_name', 'fas fa-tag', sub.category_name)}
                ${createField('subscription-next-payment', 'far fa-calendar-alt', `Следующий платеж: ${formattedDate}`)}
                ${createField(amountClass, 'fas fa-money-bill-wave', `${sub.amount} ${sub.currency}`)}
            `;

            // Добавляем информацию о банке и карте, только если они указаны
            if (sub.bank) {
                subscriptionHTML += createField('subscription-bank', 'fas fa-university', sub.bank);
            }
            if (sub.card_last_4) {
                subscriptionHTML += createField('subscription-card', 'far fa-credit-card', `**** ${sub.card_last_4}`);
            }

            // Добавляем меню подписки с иконками
            subscriptionHTML += `
                <div class="subscription-menu" id="menu-${sub.id}" style="display: none;">
                    <button onclick="editSubscription(${sub.id})">
                        <i class="fas fa-edit"></i> Редактировать
                    </button>
                    <button onclick="archiveSubscription(${sub.id})">
                        <i class="fas fa-archive"></i> Архивировать
                    </button>
                    <button onclick="deleteSubscription(${sub.id})">
                        <i class="fas fa-trash-alt"></i> Удалить
                    </button>
                </div>
            `;

            subElement.innerHTML = subscriptionHTML;
            subscriptionsList.appendChild(subElement);
        });

        elements.subscriptions.appendChild(subscriptionsList);
        debugLog(`Отображено ${subscriptions.length} подписок`);

        // Добавляем сортировку подписок
        const sortSubscriptions = (sortBy) => {
            debugLog(`Сортировка подписок по ${sortBy}`);
            const items = Array.from(subscriptionsList.children);
            items.sort((a, b) => {
                if (sortBy === 'next_payment') {
                    const aDate = new Date(a.querySelector('.subscription-next-payment .field-content').textContent.split(': ')[1]);
                    const bDate = new Date(b.querySelector('.subscription-next-payment .field-content').textContent.split(': ')[1]);
                    return aDate - bDate;
                } else if (sortBy === 'amount') {
                    const aAmount = parseFloat(a.querySelector('.subscription-amount .field-content').textContent);
                    const bAmount = parseFloat(b.querySelector('.subscription-amount .field-content').textContent);
                    return aAmount - bAmount;
                }
            });
            items.forEach(item => subscriptionsList.appendChild(item));

            // Обновляем активную кнопку сортировки
            document.querySelectorAll('.sort-button').forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.sort === sortBy) {
                    btn.classList.add('active');
                }
            });
        };

        // Добавляем кнопки сортировки
        const sortButtons = document.createElement('div');
        sortButtons.className = 'sort-buttons';
        sortButtons.innerHTML = `
            <button class="sort-button" data-sort="next_payment">По дате</button>
            <button class="sort-button" data-sort="amount">По сумме</button>
        `;
        sortButtons.querySelectorAll('.sort-button').forEach(btn => {
            btn.addEventListener('click', () => sortSubscriptions(btn.dataset.sort));
        });
        elements.subscriptions.insertBefore(sortButtons, subscriptionsList);
    }
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
        displaySubscriptions(subscriptions);
    } catch (error) {
        debugLog(`Ошибка при обновлении списка подписок: ${error.message}`);
        console.error('Error updating subscriptions list:', error);
    }
}

// Показать модальное окно
function toggleAddSubscriptionForm(show) {
    const addSubscriptionForm = document.getElementById('add-subscription-form');
    const subscriptionsList = document.getElementById('subscriptions');

    if (show) {
        addSubscriptionForm.style.display = 'block';
        subscriptionsList.style.display = 'none';
        resetForm();
        currentSlide = 1;
        showSlide(currentSlide);
        updateProgressBar();
        updateNavigationButtons();
        toggleNavbar(false);

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
    return date >= today;
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

// Инициализация нижней навигации
function initNavbar() {
    debugLog('Инициализация навигационной панели');

    const navItems = document.querySelectorAll('.nav-item');
    const navIndicator = document.querySelector('.nav-indicator');
    const navActions = {
        'navSubscriptions': fetchSubscriptions,
        'navAddSubscription': () => {
            debugLog('Нажата кнопка добавления подписки');
            toggleAddSubscriptionForm(true);
        },
        'navCalendar': () => {
            debugLog('Нажата кнопка календаря');
            // Здесь можно добавить логику для отображения календаря
        }
    };

    function setIndicatorPosition(item) {
        const itemRect = item.getBoundingClientRect();
        const navbarRect = item.closest('.bottom-navbar').getBoundingClientRect();

        navIndicator.style.width = `${itemRect.width}px`;
        navIndicator.style.left = `${itemRect.left - navbarRect.left}px`;
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            setIndicatorPosition(item);
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
        const clearButton = document.getElementById('clear-debug');
        if (clearButton) {
            clearButton.addEventListener('click', clearDebugOutput);
        }
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
    } else {
        navbar.style.display = 'none';
    }
}

async function editSubscription(subscriptionId) {
    const subscriptionItem = document.querySelector(`.subscription-item[data-id="${subscriptionId}"]`);
    if (!subscriptionItem) return;

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
            <input type="text" id="edit-custom-service" style="display: none;" placeholder="Введите название сервиса">
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

    editServiceSelect.addEventListener('change', function() {
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
    anime({
        targets: editForm,
        opacity: [0, 1],
        translateY: [-20, 0],
        duration: 500,
        easing: 'easeOutCubic',
        begin: function(anim) {
            editForm.style.display = 'block';
        }
    });

    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const updatedData = {
            service_name: editServiceSelect.value === 'custom' ? editCustomServiceInput.value : editServiceSelect.value,
            category_name: editCategorySelect.value,
            amount: parseFloat(editForm.querySelector('#edit-amount').value),
            currency: editForm.querySelector('#edit-currency').value
        };

        try {
            const response = await fetch(`/update_subscription/${subscriptionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updatedData),
            });

            if (response.ok) {
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
// Инициализация приложения при загрузке
document.addEventListener('DOMContentLoaded', () => {
    init().catch(error => console.error('Error in init:', error));
});