let currentStep = 1;
const totalSteps = 4;

function nextStep() {
    if (validateCurrentStep()) {
        if (currentStep < totalSteps) {
            updateReview();
            currentStep++;
            showStep(currentStep);
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        showStep(currentStep);
    }
}

function showStep(step) {
    // Hide all steps
    document.querySelectorAll('.wizard-step').forEach(s => {
        s.classList.remove('active');
    });
    
    // Show current step
    document.getElementById(`step-${step}`).classList.add('active');
    
    // Update step indicator
    document.querySelectorAll('.step').forEach((s, index) => {
        const stepNum = index + 1;
        s.classList.remove('active', 'completed');
        if (stepNum < step) {
            s.classList.add('completed');
        } else if (stepNum === step) {
            s.classList.add('active');
        }
    });
}

function validateCurrentStep() {
    const step = document.getElementById(`step-${currentStep}`);
    const requiredFields = step.querySelectorAll('[required]');
    
    for (let field of requiredFields) {
        if (!field.value.trim()) {
            alert(`Please fill in ${field.previousElementSibling?.textContent || 'all required fields'}`);
            field.focus();
            return false;
        }
    }
    
    // Special validation for step 2
    if (currentStep === 2) {
        const connectionType = document.querySelector('input[name="db-connection-type"]:checked').value;
        if (connectionType === 'string') {
            const connString = document.getElementById('connection-string').value;
            if (!connString) {
                alert('Please provide a connection string');
                return false;
            }
        } else {
            const host = document.getElementById('db-host').value;
            const user = document.getElementById('db-user').value;
            const password = document.getElementById('db-password').value;
            const database = document.getElementById('db-database').value;
            if (!host || !user || !password || !database) {
                alert('Please fill in all required database fields');
                return false;
            }
        }
    }
    
    return true;
}

function toggleConnectionType() {
    const connectionType = document.querySelector('input[name="db-connection-type"]:checked').value;
    const stringGroup = document.getElementById('connection-string-group');
    const paramsGroup = document.getElementById('connection-params-group');
    
    if (connectionType === 'string') {
        stringGroup.style.display = 'block';
        paramsGroup.style.display = 'none';
    } else {
        stringGroup.style.display = 'none';
        paramsGroup.style.display = 'block';
    }
}

async function testConnection() {
    const statusEl = document.getElementById('connection-status');
    statusEl.textContent = 'Testing...';
    statusEl.className = '';
    
    const connectionType = document.querySelector('input[name="db-connection-type"]:checked').value;
    let dbConfig = {};
    
    if (connectionType === 'string') {
        dbConfig.connection_string = document.getElementById('connection-string').value;
    } else {
        dbConfig.host = document.getElementById('db-host').value;
        dbConfig.port = parseInt(document.getElementById('db-port').value) || 5432;
        dbConfig.user = document.getElementById('db-user').value;
        dbConfig.password = document.getElementById('db-password').value;
        dbConfig.database = document.getElementById('db-database').value;
    }
    
    try {
        const response = await fetch('/api/databases/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dbConfig)
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            statusEl.textContent = '✓ Connection successful!';
            statusEl.className = 'success';
        } else {
            statusEl.textContent = '✗ Connection failed: ' + (data.message || data.error);
            statusEl.className = 'error';
        }
    } catch (error) {
        statusEl.textContent = '✗ Error testing connection';
        statusEl.className = 'error';
        console.error('Connection test error:', error);
    }
}

function updateReview() {
    // Agent Info
    const agentId = document.getElementById('agent-id').value;
    const agentName = document.getElementById('agent-name').value;
    const agentType = document.getElementById('agent-type').value;
    
    document.getElementById('review-agent-info').innerHTML = `
        <div class="review-item"><strong>Agent ID:</strong> ${agentId}</div>
        <div class="review-item"><strong>Name:</strong> ${agentName || 'Not specified'}</div>
        <div class="review-item"><strong>Type:</strong> ${agentType}</div>
    `;
    
    // Database Info
    const connectionType = document.querySelector('input[name="db-connection-type"]:checked').value;
    let dbInfo = '';
    
    if (connectionType === 'string') {
        const connString = document.getElementById('connection-string').value;
        dbInfo = `<div class="review-item"><strong>Connection:</strong> ${connString.replace(/:[^:@]*@/, ':****@')}</div>`;
    } else {
        const host = document.getElementById('db-host').value;
        const port = document.getElementById('db-port').value;
        const user = document.getElementById('db-user').value;
        const database = document.getElementById('db-database').value;
        dbInfo = `
            <div class="review-item"><strong>Host:</strong> ${host}</div>
            <div class="review-item"><strong>Port:</strong> ${port}</div>
            <div class="review-item"><strong>User:</strong> ${user}</div>
            <div class="review-item"><strong>Database:</strong> ${database}</div>
        `;
    }
    
    document.getElementById('review-database-info').innerHTML = dbInfo;
    
    // Credentials Info
    const apiKey = document.getElementById('agent-api-key').value;
    document.getElementById('review-credentials-info').innerHTML = `
        <div class="review-item"><strong>API Key:</strong> ${apiKey.substring(0, 20)}...</div>
        <div class="review-item"><strong>API Secret:</strong> ••••••••</div>
    `;
}

// Form submission
document.getElementById('wizard-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Connecting...';
    
    // Collect form data
    const formData = {
        agent_id: document.getElementById('agent-id').value,
        agent_info: {
            name: document.getElementById('agent-name').value,
            type: document.getElementById('agent-type').value
        },
        agent_credentials: {
            api_key: document.getElementById('agent-api-key').value,
            api_secret: document.getElementById('agent-api-secret').value
        }
    };
    
    // Database config
    const connectionType = document.querySelector('input[name="db-connection-type"]:checked').value;
    if (connectionType === 'string') {
        formData.database = {
            connection_string: document.getElementById('connection-string').value
        };
    } else {
        formData.database = {
            host: document.getElementById('db-host').value,
            port: parseInt(document.getElementById('db-port').value) || 5432,
            user: document.getElementById('db-user').value,
            password: document.getElementById('db-password').value,
            database: document.getElementById('db-database').value
        };
    }
    
    try {
        const response = await fetch('/api/agents/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show success message
            document.querySelector('.wizard-form').style.display = 'none';
            document.getElementById('success-message').style.display = 'block';
            
            document.getElementById('success-details').innerHTML = `
                <p><strong>Agent ID:</strong> ${data.agent_id}</p>
                <p><strong>API Key:</strong> <code>${data.api_key}</code></p>
                <p class="info">Save this API key - you'll need it for agent authentication!</p>
            `;
        } else {
            alert('Error: ' + (data.error || data.message || 'Failed to register agent'));
            submitBtn.disabled = false;
            submitBtn.textContent = 'Connect Agent';
        }
    } catch (error) {
        alert('Error connecting agent: ' + error.message);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Connect Agent';
    }
});

