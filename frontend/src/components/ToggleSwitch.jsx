import React from 'react';

export function ToggleSwitch({ isChecked, onToggle }) {
  return (
    <label className="toggle-switch">
      <input
        type="checkbox"
        className="toggle-switch-input"
        checked={isChecked}
        onChange={() => onToggle(!isChecked)}
      />
      <div className="toggle-switch-track">
        <div className="toggle-switch-nub"></div>
      </div>
    </label>
  );
}