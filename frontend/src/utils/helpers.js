// Format date to YYYY-MM-DD
export const formatDate = (date) => {
    return new Date(date).toISOString().split('T')[0];
  };
  
  // Convert file size to human readable format
  export const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  // Validate file type
  export const isValidFileType = (file, types) => {
    return types.includes(file.type);
  }; 