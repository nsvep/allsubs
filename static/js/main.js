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
    subscriptionModal: document.getElementById('subscriptionModal'),
    serviceSelect: document.getElementById('serviceSelect'),
    customService: document.getElementById('customService'),
    categorySelect: document.getElementById('categorySelect'),
    modalTitle: document.getElementById('modalTitle'),
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

// Инициализация приложения
async function init() {
    debugLog('Инициализация приложения начата');
    const telegramUser = tg.initDataUnsafe?.user;
    if (!telegramUser) {
        debugLog('Ошибка: данные пользователя Telegram не найдены');
        console.error('Telegram User data not found');
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

            // Параллельная загрузка данных
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

                elements.serviceSelect.addEventListener('change', onServiceChange);
                elements.prevSlide.addEventListener('click', prevSlide);
                elements.nextSlide.addEventListener('click', nextSlide);
                elements.skipSlide.addEventListener('click', skipSlide);
                document.querySelector('.close').addEventListener('click', closeModal);
                debugLog('Инициализация приложения завершена успешно');
            } catch (error) {
                debugLog(`Ошибка при загрузке данных: ${error.message}`);
                console.error('Error loading data:', error);
            }
        } else {
            debugLog('Ошибка при получении информации о пользователе');
            throw new Error('Failed to get user info');
        }
    } catch (error) {
        debugLog(`Ошибка при инициализации: ${error.message}`);
        console.error('Initialization error:', error);
    }
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
    elements.subscriptions.innerHTML = '';
    if (subscriptions.length === 0) {
        const noSubscriptionsElement = document.createElement('div');
        noSubscriptionsElement.className = 'no-subscriptions';
        noSubscriptionsElement.innerHTML = `
                <div class="illustration">
                <i class="fas fa-list-alt"></i>
                <h2>Нет активных подписок</h2>
                <p>Добавьте свою первую подписку, используя кнопку "+" в нижнем меню.</p>
            </div>
        `;
        elements.subscriptions.appendChild(noSubscriptionsElement);
    } else {
        const subscriptionsList = document.createElement('div');
        subscriptionsList.className = 'subscriptions-list';

        subscriptions.forEach(sub => {
            const subElement = document.createElement('div');
            subElement.className = 'subscription-item';

            // Форматируем дату следующего платежа
            const nextPaymentDate = new Date(sub.start_date);
            const formattedDate = nextPaymentDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });

            // Определяем класс для суммы (для возможной цветовой индикации)
            const amountClass = sub.amount > 1000 ? 'subscription-amount high' : 'subscription-amount';

            subElement.innerHTML = `
                <div class="subscription-header">
                    <h3>${sub.service_name}</h3>
                    <button class="btn-more" onclick="showSubscriptionMenu(${sub.id})">⋮</button>
                </div>
                <p class="subscription-category"><i class="fas fa-tag"></i> ${sub.category_name}</p>
                <p class="subscription-next-payment"><i class="far fa-calendar-alt"></i> Следующий платеж: ${formattedDate}</p>
                <p class="${amountClass}"><i class="fas fa-money-bill-wave"></i> ${sub.amount} ${sub.currency}</p>
                <div id="menu-${sub.id}" class="subscription-menu">
                    <button onclick="editSubscription(${sub.id})"><i class="fas fa-edit"></i> Редактировать</button>
                    <button onclick="archiveSubscription(${sub.id})"><i class="fas fa-archive"></i> Архивировать</button>
                    <button onclick="deleteSubscription(${sub.id})"><i class="fas fa-trash-alt"></i> Удалить</button>
                </div>
            `;
            subscriptionsList.appendChild(subElement);
        });

        elements.subscriptions.appendChild(subscriptionsList);
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
    menu.style.display = menu.style.display === 'block' ? 'none' : 'block';

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
            closeModal();
            await updateSubscriptionsList();
            tg.showPopup({message: subscriptionId ? 'Подписка обновлена' : 'Подписка добавлена'});
        } else {
            debugLog(`Ошибка при сохранении подписки: ${result.message}`);
            throw new Error(result.message || 'Failed to save subscription');
        }
    } catch (error) {
        debugLog(`Ошибка при сохранении подписки: ${error.message}`);
        console.error('Error saving subscription:', error);
        tg.showPopup({message: 'Ошибка при сохранении подписки: ' + error.message});
    } finally {
        isSaving = false; // Сбрасываем флаг сохранения
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
function showModal(title) {
    elements.modalTitle.textContent = title;
    elements.subscriptionModal.style.display = 'block';
    toggleNavbar(false); // Скрываем navbar
    tg.MainButton.setText('Сохранить');
    tg.MainButton.show();
}

// Закрыть модальное окно
function closeModal() {
    elements.subscriptionModal.style.display = 'none';
    toggleNavbar(true); // Показываем navbar
    tg.MainButton.hide();
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
}

// Показать слайд
function showSlide(slideNumber) {
    const slides = document.querySelectorAll('.slide');
    slides.forEach((slide, index) => {
        slide.style.display = index + 1 === slideNumber ? 'block' : 'none';
    });
    updateNavigationButtons(slideNumber);
}

// Обновление кнопок навигации
function updateNavigationButtons(slideNumber) {
    elements.prevSlide.style.display = slideNumber > 1 ? 'inline-block' : 'none';
    elements.nextSlide.style.display = slideNumber < 3 ? 'inline-block' : 'none';
    elements.skipSlide.style.display = slideNumber === 3 ? 'inline-block' : 'none';

    // Показываем кнопку Telegram только на последнем слайде
    if (slideNumber === 3) {
        tg.MainButton.setText('Добавить');
        tg.MainButton.show();
    } else {
        tg.MainButton.hide();
    }
}

// Предыдущий слайд
function prevSlide() {
    if (currentSlide > 1) {
        currentSlide--;
        showSlide(currentSlide);
    }
}

// Следующий слайд
function nextSlide() {
    if (validateSlide(currentSlide)) {
        if (currentSlide < 3) {
            currentSlide++;
            showSlide(currentSlide);
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
                tg.showPopup({ message: 'Пожалуйста, выберите сервис' });
                return false;
            }
            if (elements.serviceSelect.value === 'custom' && !isValidString(elements.customService.value, 2, 50)) {
                tg.showPopup({ message: 'Название сервиса должно содержать от 2 до 50 символов' });
                return false;
            }
            if (elements.serviceSelect.value === 'custom' && !isValidSelect(elements.categorySelect.value)) {
                tg.showPopup({ message: 'Пожалуйста, выберите категорию для кастомного сервиса' });
                return false;
            }
            break;

        case 2:
            if (!isValidDate(elements.nextPaymentDate.value)) {
                tg.showPopup({ message: 'Дата следующего платежа не может быть в прошлом' });
                return false;
            }
            if (!isValidAmount(elements.amount.value)) {
                tg.showPopup({ message: 'Пожалуйста, введите корректную сумму' });
                return false;
            }
            if (!isValidSelect(elements.currency.value)) {
                tg.showPopup({ message: 'Пожалуйста, выберите валюту' });
                return false;
            }
            break;

        case 3:
            if (elements.bank.value && !isValidString(elements.bank.value, 2, 50)) {
                tg.showPopup({ message: 'Название банка должно содержать от 2 до 50 символов' });
                return false;
            }
            if (elements.cardLast4.value && !isValidCardLast4(elements.cardLast4.value)) {
                tg.showPopup({ message: 'Последние 4 цифры карты должны содержать 4 цифры' });
                return false;
            }
            break;

        default:
            console.error('Неизвестный номер слайда:', slideNumber);
            return false;
    }

    return true;
}

// Пропустить слайд
function skipSlide() {
    saveSubscription();
}

// Инициализация нижней навигации
function initNavbar() {
    const navActions = {
        'navSubscriptions': fetchSubscriptions,
        'navAddSubscription': () => {
            showModal('Добавить подписку');
            resetForm();
            currentSlide = 1;
            showSlide(currentSlide);
        },
        'navCalendar': showCalendar
    };

    Object.entries(navActions).forEach(([id, action]) => {
        document.getElementById(id).addEventListener('click', action);
    });

    // Обработчик для кнопки Telegram
    tg.MainButton.onClick(() => {
        if (!isSaving) {
            saveSubscription();
        }
    });
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
    if (debugOutput && userId === 3) {
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

// Инициализация приложения при загрузке
document.addEventListener('DOMContentLoaded', () => {
    init().catch(error => console.error('Error in init:', error));
});