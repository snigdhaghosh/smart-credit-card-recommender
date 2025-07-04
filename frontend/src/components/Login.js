import React, { useState } from 'react';

const Login = ({ onLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    // const handleLogin = async (e) => {
    //     e.preventDefault();
    //     setError('');

    //     try {
    //         const response = await fetch('http://127.0.0.1:5000/api/login', {
    //             method: 'POST',
    //             headers: { 'Content-Type': 'application/json' },
    //             body: JSON.stringify({ email, password }),
    //             credentials: 'include',
    //         });
    //         const data = await response.json();

    //         if (!response.ok) {
    //             throw new Error(data.error || 'Failed to log in');
    //         }
        
    //         // On successful login, reload the page to update the user state
    //         window.location.reload();

    //     } catch (err) {
    //         setError(err.message);
    //     }
    // };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      // Call the onLogin function from the App component and pass the credentials.
      await onLogin(email, password);
    } catch (err) {
      // If the login fails, display the error message.
      setError(err.message);
    }
  };

  return (
    <div className="auth-form">
      <h3>Login</h3>
      <form onSubmit={handleSubmit}>
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
        <button type="submit">Login</button>
        {error && <p className="error-message">{error}</p>}
      </form>
    </div>
  );
};

export default Login;