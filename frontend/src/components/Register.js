// frontend/src/components/Register.js

import React, { useState } from 'react';

// It receives an `onRegister` function and a `toggleView` function from props.
const Register = ({ onRegister, toggleView }) => {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      await onRegister(username, email, password);
      setSuccess('Registration successful! Please log in.');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-form">
      <h3>Create an Account</h3>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          required
        />
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
        />
        <button type="submit">Register</button>
        {error && <p className="error-message">{error}</p>}
        {success && <p className="success-message">{success}</p>}
      </form>
      <button onClick={toggleView} className="toggle-auth-button">
        Already have an account? Login
      </button>
    </div>
  );
};

export default Register;