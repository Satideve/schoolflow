// C:\coding_projects\dev\schoolflow\frontend\src\components\ui\skeleton.tsx
import React from "react";

export const Skeleton: React.FC<{ className?: string }> = ({ className = "" }) => {
  return <div className={`animate-pulse bg-gray-200 dark:bg-gray-700 rounded ${className}`} />;
};

export default Skeleton;
