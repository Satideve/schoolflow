// C:\coding_projects\dev\schoolflow\frontend\src\components\ui\card.tsx
import React from "react";

export const Card: React.FC<{ children?: React.ReactNode; className?: string }> = ({ children, className = "" }) => {
  return <div className={`bg-white dark:bg-gray-800 shadow-sm rounded-lg p-4 ${className}`}>{children}</div>;
};

export default Card;
