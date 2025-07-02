// frontend/src/components/Card.js

import React from 'react';
import './card.css';

const Card = ({ card, isBestOption }) => {
  if (!card) {
    return null;
  }

  return (
    <div className={`card ${isBestOption ? 'best-option' : ''}`}>
      {isBestOption && <div className="best-option-badge">✨ Best Option</div>}
      <img src={card.img_url} alt={`${card.name}`} className="card-image" />
      <div className="card-body">
        <h5 className="card-title">{card.name}</h5>
        <h6 className="card-issuer">{card.issuer}</h6>
        <p className="card-text">{card.benefits_summary}</p>
        <ul className="card-details">
          <li><strong>Annual Fee:</strong> ${card.annual_fee}</li>
          {card.is_owned && <li className="owned-badge">✅ You Own This Card</li>}
        </ul>
      </div>
    </div>
  );
};

export default Card;