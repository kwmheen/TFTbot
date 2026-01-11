// CSV Save/Load functionality
function getCSVContent() {
    const controlBars = document.querySelectorAll('#control-bars-container .control-bar');
    const csvData = [];
    
    // CSV 헤더
    csvData.push('정의된 명령어,adb 명령어');
    
    // 각 컨트롤 바의 데이터 수집
    controlBars.forEach(bar => {
        const commandName = bar.querySelector('.defined-command').textContent.trim();
        const adbCommand = bar.querySelector('.adb-command').textContent.trim();
        if (commandName && adbCommand) {
            // CSV 형식: 쉼표와 따옴표 처리
            const escapedCommandName = commandName.includes(',') ? `"${commandName}"` : commandName;
            const escapedAdbCommand = adbCommand.includes(',') ? `"${adbCommand}"` : adbCommand;
            csvData.push(`${escapedCommandName},${escapedAdbCommand}`);
        }
    });
    
    return csvData.join('\n');
}

async function saveToCSV() {
    const csvContent = getCSVContent();
    
    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ csvContent: csvContent })
        });
        
        const result = await response.json();
        if (result.success) {
            alert('CSV 파일이 저장되었습니다.');
        } else {
            alert('CSV 파일 저장에 실패했습니다: ' + result.error);
        }
    } catch (error) {
        console.error('Error saving CSV:', error);
        alert('CSV 파일 저장 중 오류가 발생했습니다.');
    }
}

async function saveToLocalStorage() {
    const csvContent = getCSVContent();
    
    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ csvContent: csvContent })
        });
        
        const result = await response.json();
        if (!result.success) {
            console.error('Failed to save CSV:', result.error);
        }
    } catch (error) {
        console.error('Error saving CSV:', error);
    }
}

function loadFromCSV(csvContent, saveAfterLoad = true) {
    const lines = csvContent.split('\n').filter(line => line.trim());
    if (lines.length < 2) return; // 헤더만 있으면 리턴
    
    const controlBarsContainer = document.getElementById('control-bars-container');
    controlBarsContainer.innerHTML = ''; // 기존 컨트롤 바 제거
    
    // 헤더 제외하고 파싱
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        // CSV 파싱 (쉼표로 분리, 따옴표 처리)
        const matches = line.match(/(".*?"|[^,]+)(?=\s*,|\s*$)/g);
        if (matches && matches.length >= 2) {
            let commandName = matches[0].trim().replace(/^"|"$/g, '');
            let adbCommand = matches[1].trim().replace(/^"|"$/g, '');
            
            createControlBar(commandName, adbCommand, saveAfterLoad);
        }
    }
}

function createControlBar(commandName, adbCommand, saveAfterCreate = true) {
    const controlBarsContainer = document.getElementById('control-bars-container');
    const newControlBar = document.createElement('div');
    newControlBar.className = 'control-bar';
    
    newControlBar.innerHTML = `
        <div class="control-bar-content">
            <span class="defined-command">${commandName}</span>
            <span class="adb-command">${adbCommand}</span>
            <button class="action-button modify-button">Modify</button>
            <button class="action-button debug-button">Debug</button>
        </div>
    `;

    // Initialize inline editing for new control bar
    const newDefinedCommand = newControlBar.querySelector('.defined-command');
    const newAdbCommand = newControlBar.querySelector('.adb-command');
    makeEditable(newDefinedCommand, true);
    makeEditable(newAdbCommand, false);

    // Add event listeners for Debug button
    const debugBtn = newControlBar.querySelector('.debug-button');
    debugBtn.addEventListener('click', function() {
        const currentAdbCommand = newControlBar.querySelector('.adb-command').textContent;
        alert(`테스트 실행: ${currentAdbCommand}`);
        // 여기에 실제 adb 명령어 실행 로직을 추가할 수 있습니다
    });

    // Modify button - adb 명령어를 편집 모드로 전환
    const modifyBtn = newControlBar.querySelector('.modify-button');
    modifyBtn.addEventListener('click', function() {
        newAdbCommand.click();
    });

    controlBarsContainer.appendChild(newControlBar);
    
    // 변경사항 저장
    if (saveAfterCreate) {
        saveToLocalStorage();
    }
}

// Inline editing functionality
function makeEditable(element, isCommandName = false) {
    element.addEventListener('click', function(e) {
        // Prevent event bubbling if already editing
        if (this.querySelector('input')) return;
        
        const currentValue = this.textContent.trim();
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentValue;
        input.className = 'inline-input';
        if (isCommandName) {
            input.classList.add('defined-command-input');
        } else {
            input.classList.add('adb-command-input');
        }
        
        // Replace span with input
        const originalElement = this;
        const parent = this.parentElement;
        this.style.display = 'none';
        parent.insertBefore(input, this);
        input.focus();
        input.select();
        
        // Save on Enter or blur
        const saveEdit = () => {
            const newValue = input.value.trim();
            if (newValue !== '') {
                originalElement.textContent = newValue;
                // 인라인 편집 후 자동 저장
                saveToLocalStorage();
            }
            input.remove();
            originalElement.style.display = '';
        };
        
        const cancelEdit = () => {
            input.remove();
            originalElement.style.display = '';
        };
        
        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveEdit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelEdit();
            }
        });
    });
}

// Navigation functionality
document.addEventListener('DOMContentLoaded', function() {
    const navButtons = document.querySelectorAll('.nav-button');
    const contentSections = document.querySelectorAll('.content-section');

    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetSection = this.getAttribute('data-section');

            // Remove active class from all buttons
            navButtons.forEach(btn => btn.classList.remove('active'));

            // Add active class to clicked button
            this.classList.add('active');

            // Hide all sections
            contentSections.forEach(section => {
                section.style.display = 'none';
            });

            // Show target section
            const targetElement = document.getElementById(targetSection);
            if (targetElement) {
                targetElement.style.display = 'block';
            }
        });
    });

    // Initialize inline editing for existing elements
    const addControlBar = document.querySelector('.add-control-bar');
    const addDefinedCommand = addControlBar.querySelector('.defined-command');
    const addAdbCommand = addControlBar.querySelector('.adb-command');
    
    makeEditable(addDefinedCommand, true);
    makeEditable(addAdbCommand, false);

    // Add Control Bar functionality
    const addButton = document.querySelector('.add-button');
    const controlBarsContainer = document.getElementById('control-bars-container');

    addButton.addEventListener('click', function() {
        const addBar = document.querySelector('.add-control-bar');
        const commandName = addBar.querySelector('.defined-command').textContent.trim();
        const adbCommand = addBar.querySelector('.adb-command').textContent.trim();

        // Only add if both fields have meaningful content
        if (commandName && commandName !== 'Title' && adbCommand && adbCommand !== 'command') {
            createControlBar(commandName, adbCommand);

            // Reset add control bar
            addBar.querySelector('.defined-command').textContent = 'Title';
            addBar.querySelector('.adb-command').textContent = 'command';
        }
    });

    // CSV Save button
    const saveCsvBtn = document.getElementById('save-csv-btn');
    saveCsvBtn.addEventListener('click', saveToCSV);

    // 페이지 로드 시 항상 controlbar.csv를 서버에서 불러오기
    async function loadFromServer() {
        try {
            const response = await fetch('/api/load');
            const result = await response.json();
            
            if (result.success && result.data) {
                loadFromCSV(result.data, false);
            }
        } catch (error) {
            console.error('Error loading CSV:', error);
        }
    }
    
    loadFromServer();
});
