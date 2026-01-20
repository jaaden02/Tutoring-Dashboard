// Tutoring Dashboard - Main JavaScript

class Dashboard {
  constructor() {
    this.quickRange = 'all';
    this.startDate = null;
    this.endDate = null;
    this.monthlyChart = null;
    this.topStudentsChart = null;
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.loadData();
    // Auto-refresh every 60 seconds
    setInterval(() => this.loadData(), 60000);
  }

  setupEventListeners() {
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
      this.refreshData();
    });

    // Quick range filter
    document.getElementById('quick-range').addEventListener('change', (e) => {
      this.quickRange = e.target.value;
      this.loadData();
    });

    // Date filters
    document.getElementById('start-date').addEventListener('change', (e) => {
      this.startDate = e.target.value;
      if (this.startDate && this.endDate) {
        this.quickRange = 'custom';
        this.loadData();
      }
    });

    document.getElementById('end-date').addEventListener('change', (e) => {
      this.endDate = e.target.value;
      if (this.startDate && this.endDate) {
        this.quickRange = 'custom';
        this.loadData();
      }
    });

    // Modal close
    document.querySelector('.modal-close').addEventListener('click', () => {
      document.getElementById('student-modal').style.display = 'none';
    });

    window.addEventListener('click', (e) => {
      const modal = document.getElementById('student-modal');
      if (e.target === modal) {
        modal.style.display = 'none';
      }
    });

    // Student search (debounced)
    const searchInput = document.getElementById('student-search');
    if (searchInput) {
      let debounceTimer;
      searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          this.performStudentSearch(query);
        }, 300);
      });
    }
  }

  async loadData() {
    try {
      await Promise.all([
        this.loadMetrics(),
        this.loadTopStudents(),
        this.loadMonthlySummary()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
      this.showError('Failed to load dashboard data');
    }
  }

  async loadMetrics() {
    try {
      const params = new URLSearchParams({
        quick_range: this.quickRange
      });

      if (this.quickRange === 'custom' && this.startDate && this.endDate) {
        params.set('start_date', this.startDate);
        params.set('end_date', this.endDate);
      }

      const response = await fetch(`/api/metrics?${params}`);
      if (!response.ok) throw new Error('Failed to fetch metrics');
      
      const metrics = await response.json();
      this.updateMetrics(metrics);
    } catch (error) {
      console.error('Error loading metrics:', error);
    }
  }

  updateMetrics(metrics) {
    document.getElementById('total-revenue').textContent = `€${metrics.total_revenue.toFixed(2)}`;
    document.getElementById('total-hours').textContent = `${metrics.total_hours.toFixed(1)}h`;
    document.getElementById('avg-rate').textContent = `€${metrics.avg_hourly_rate.toFixed(2)}`;
    document.getElementById('unique-students').textContent = metrics.unique_students;
    document.getElementById('total-sessions').textContent = metrics.total_sessions;
    document.getElementById('avg-session').textContent = `${metrics.avg_session_length.toFixed(1)}h`;
    document.getElementById('this-month-revenue').textContent = `€${metrics.this_month_revenue.toFixed(2)}`;
    document.getElementById('this-month-hours').textContent = `${metrics.this_month_hours.toFixed(1)}h`;

    // Animate numbers
    this.animateMetrics();
  }

  animateMetrics() {
    const cards = document.querySelectorAll('.metric-card');
    cards.forEach((card, index) => {
      card.style.animation = 'none';
      setTimeout(() => {
        card.style.animation = `fadeIn 0.4s ease ${index * 0.05}s backwards`;
      }, 10);
    });
  }

  async loadTopStudents() {
    try {
      const response = await fetch('/api/top-students');
      if (!response.ok) throw new Error('Failed to fetch top students');
      
      const students = await response.json();
      this.updateTopStudents(students);
      this.renderTopStudentsChart(students);
    } catch (error) {
      console.error('Error loading top students:', error);
    }
  }

  updateTopStudents(students) {
    const tbody = document.getElementById('top-students-body');
    tbody.innerHTML = '';

    students.forEach((student, index) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${index + 1}</td>
        <td><strong>${student.Name}</strong></td>
        <td>€${student.Lohn.toFixed(2)}</td>
        <td>${student.Stunden.toFixed(1)}h</td>
        <td>${student.Sessions}</td>
        <td>€${(student.Lohn / student.Stunden).toFixed(2)}/h</td>
      `;
      row.addEventListener('click', () => this.showStudentDetails(student.Name));
      tbody.appendChild(row);
    });
  }

  async showStudentDetails(studentName) {
    try {
      const response = await fetch(`/api/student-details/${encodeURIComponent(studentName)}`);
      if (!response.ok) throw new Error('Failed to fetch student details');
      
      const details = await response.json();
      this.displayStudentModal(details);
    } catch (error) {
      console.error('Error loading student details:', error);
      this.showError('Failed to load student details');
    }
  }

  displayStudentModal(details) {
    const modal = document.getElementById('student-modal');
    const modalName = document.getElementById('modal-student-name');
    const modalDetails = document.getElementById('modal-student-details');

    modalName.textContent = details.name;
    
    modalDetails.innerHTML = `
      <div style="margin-bottom: 24px;">
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px;">
          <div style="background: var(--background); padding: 16px; border-radius: 12px;">
            <div style="font-size: 12px; color: var(--muted); margin-bottom: 4px;">Total Revenue</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--primary);">€${details.total_revenue.toFixed(2)}</div>
          </div>
          <div style="background: var(--background); padding: 16px; border-radius: 12px;">
            <div style="font-size: 12px; color: var(--muted); margin-bottom: 4px;">Total Hours</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--primary);">${details.total_hours.toFixed(1)}h</div>
          </div>
          <div style="background: var(--background); padding: 16px; border-radius: 12px;">
            <div style="font-size: 12px; color: var(--muted); margin-bottom: 4px;">Sessions</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--primary);">${details.total_sessions}</div>
          </div>
          <div style="background: var(--background); padding: 16px; border-radius: 12px;">
            <div style="font-size: 12px; color: var(--muted); margin-bottom: 4px;">Avg Rate</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--primary);">€${details.avg_hourly_rate.toFixed(2)}</div>
          </div>
        </div>
        
        <h3 style="margin-bottom: 12px; font-size: 18px;">Recent Sessions</h3>
        <div style="max-height: 300px; overflow-y: auto;">
          <table style="width: 100%; font-size: 13px;">
            <thead style="position: sticky; top: 0; background: var(--surface);">
              <tr>
                <th style="padding: 8px; text-align: left;">Date</th>
                <th style="padding: 8px; text-align: left;">Hours</th>
                <th style="padding: 8px; text-align: left;">Revenue</th>
              </tr>
            </thead>
            <tbody>
              ${details.sessions.map(session => `
                <tr style="border-bottom: 1px solid var(--border);">
                  <td style="padding: 8px;">${new Date(session.Datum).toLocaleDateString()}</td>
                  <td style="padding: 8px;">${session.Stunden.toFixed(1)}h</td>
                  <td style="padding: 8px;">€${session.Lohn.toFixed(2)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;

    modal.style.display = 'block';
  }

  async refreshData() {
    const btn = document.getElementById('refresh-btn');
    btn.classList.add('loading');
    btn.disabled = true;

    try {
      const response = await fetch('/api/refresh');
      if (!response.ok) throw new Error('Failed to refresh data');
      
      await this.loadData();
      this.showSuccess('Data refreshed successfully');
    } catch (error) {
      console.error('Error refreshing data:', error);
      this.showError('Failed to refresh data');
    } finally {
      btn.classList.remove('loading');
      btn.disabled = false;
    }
  }

  async loadMonthlySummary() {
    try {
      const params = new URLSearchParams({
        quick_range: this.quickRange
      });
      if (this.quickRange === 'custom' && this.startDate && this.endDate) {
        params.set('start_date', this.startDate);
        params.set('end_date', this.endDate);
      }
      const response = await fetch(`/api/monthly-summary?${params}`);
      if (!response.ok) throw new Error('Failed to fetch monthly summary');
      const summary = await response.json();
      this.renderMonthlyChart(summary);
    } catch (error) {
      console.error('Error loading monthly summary:', error);
    }
  }

  renderMonthlyChart(summary) {
    const ctx = document.getElementById('monthly-chart');
    if (!ctx) return;
    if (this.monthlyChart) {
      this.monthlyChart.destroy();
    }
    this.monthlyChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: summary.months,
        datasets: [
          {
            label: 'Revenue (€)',
            data: summary.revenue,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            tension: 0.3,
            yAxisID: 'y',
          },
          {
            label: 'Hours',
            data: summary.hours,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.2)',
            tension: 0.3,
            yAxisID: 'y1',
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: true },
          tooltip: { enabled: true }
        },
        scales: {
          y: {
            type: 'linear',
            position: 'left',
            grid: { drawOnChartArea: false }
          },
          y1: {
            type: 'linear',
            position: 'right',
            grid: { drawOnChartArea: false }
          }
        }
      }
    });
  }

  renderTopStudentsChart(students) {
    const ctx = document.getElementById('top-students-chart');
    if (!ctx) return;
    if (this.topStudentsChart) {
      this.topStudentsChart.destroy();
    }
    const labels = students.map(s => s.Name);
    const revenue = students.map(s => s.Lohn);
    this.topStudentsChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Revenue (€)',
          data: revenue,
          backgroundColor: 'rgba(99, 102, 241, 0.6)',
          borderColor: '#6366f1',
          borderWidth: 1,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true }
        },
        scales: {
          x: { ticks: { autoSkip: false, maxRotation: 45, minRotation: 0 } },
          y: { beginAtZero: true }
        }
      }
    });
  }

  async performStudentSearch(query) {
    const resultsContainer = document.getElementById('student-results');
    if (!resultsContainer) return;
    if (!query) {
      resultsContainer.innerHTML = '';
      return;
    }
    try {
      const res = await fetch(`/api/student-search?q=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error('Search failed');
      const data = await res.json();
      const results = data.results || [];
      resultsContainer.innerHTML = results.map(name => `
        <div class="student-result-item" data-name="${name}">
          <i class="bi bi-person-circle"></i>
          <span>${name}</span>
        </div>
      `).join('');
      // Click handler
      Array.from(resultsContainer.querySelectorAll('.student-result-item')).forEach(el => {
        el.addEventListener('click', () => {
          const name = el.getAttribute('data-name');
          resultsContainer.innerHTML = '';
          document.getElementById('student-search').value = name;
          this.showStudentDetails(name);
        });
      });
    } catch (err) {
      console.error(err);
    }
  }

  showError(message) {
    // Simple toast notification (you can enhance this)
    alert(message);
  }

  showSuccess(message) {
    console.log(message);
  }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new Dashboard();
});
