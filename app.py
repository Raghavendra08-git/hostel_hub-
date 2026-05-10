{% extends 'base.html' %}

{% block content %}
<div style="max-width: 600px; margin: 0 auto;">
    <div class="card">
        <div style="text-align: center; margin-bottom: 2rem;">
            <div
                style="width: 100px; height: 100px; background: var(--gradient); border-radius: 50%; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #3b82f6, #60a5fa);">
                <span style="font-size: 2.5rem; color: white;">{{ user.name[0] }}</span>
            </div>
            <h2>{{ user.name }}</h2>
            <p style="color: var(--text-gray);">{{ user.role|capitalize }}</p>
        </div>

        <form action="{{ url_for('profile') }}" method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" value="{{ user.username }}" disabled style="opacity: 0.7;">
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" value="{{ user.email }}" disabled style="opacity: 0.7;">
            </div>
            <div class="form-group">
                <label>Phone Number</label>
                <input type="text" name="phone" value="{{ user.phone or '' }}" placeholder="Update phone number">
            </div>

            <div class="form-group" style="border-top: var(--glass-border); padding-top: 1.5rem; margin-top: 1.5rem;">
                <label>Change Password <span style="font-size: 0.8rem; color: var(--text-gray);">(Leave blank to keep
                        current)</span></label>
                <input type="password" name="password" placeholder="New Password">
            </div>

            <button type="submit" class="btn" style="width: 100%;">Update Profile</button>
        </form>
    </div>
</div>
{% endblock %}