import { useState, useMemo } from 'react';

export function useSearch<T>(
  items: T[],
  searchFields: (item: T) => string[],
) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredItems = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return items;
    return items.filter((item) =>
      searchFields(item).some((field) => field.toLowerCase().includes(query)),
    );
  }, [items, searchQuery, searchFields]);

  return { searchQuery, setSearchQuery, filteredItems };
}
