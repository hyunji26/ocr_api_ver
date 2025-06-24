import React, { createContext, useContext, useState } from 'react';

const MealContext = createContext();

export const MealProvider = ({ children }) => {
  const [shouldRefresh, setShouldRefresh] = useState(false);

  const triggerRefresh = () => {
    setShouldRefresh(prev => !prev);
  };

  return (
    <MealContext.Provider value={{ shouldRefresh, triggerRefresh }}>
      {children}
    </MealContext.Provider>
  );
};

export const useMeal = () => {
  const context = useContext(MealContext);
  if (!context) {
    throw new Error('useMeal must be used within a MealProvider');
  }
  return context;
}; 