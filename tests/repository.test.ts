import { createRepository, getRepository, updateRepository, deleteRepository } from '../api/repository/repository.service';
import { Repository } from '../api/repository/repository.model';

describe('Repository Service', () => {
  // Test data
  const testRepo = {
    name: 'Casa Verdi',
    ownerId: 'user123',
    description: 'Test repository',
    tags: ['residential', 'modern']
  };

  beforeEach(() => {
    // Clear database or mock data before each test
    jest.clearAllMocks();
  });

  describe('createRepository()', () => {
    it('should create a repository with valid data', async () => {
      const repo = await createRepository(testRepo);
      
      expect(repo).toBeDefined();
      expect(repo.name).toBe(testRepo.name);
      expect(repo.ownerId).toBe(testRepo.ownerId);
      expect(repo.description).toBe(testRepo.description);
      expect(repo.tags).toEqual(testRepo.tags);
    });

    it('should fail if repository name is missing', async () => {
      const invalidRepo = { ...testRepo, name: '' };
      await expect(createRepository(invalidRepo)).rejects.toThrow('Name is required');
    });

    it('should fail if ownerId is missing', async () => {
      const invalidRepo = { ...testRepo, ownerId: '' };
      await expect(createRepository(invalidRepo)).rejects.toThrow('Owner ID is required');
    });
  });

  describe('getRepository()', () => {
    it('should return repository by ID', async () => {
      const createdRepo = await createRepository(testRepo);
      const foundRepo = await getRepository(createdRepo.id);
      
      expect(foundRepo).toBeDefined();
      expect(foundRepo.id).toBe(createdRepo.id);
    });

    it('should return null for non-existent repository', async () => {
      const foundRepo = await getRepository('nonexistent-id');
      expect(foundRepo).toBeNull();
    });
  });

  describe('updateRepository()', () => {
    it('should update repository with valid data', async () => {
      const createdRepo = await createRepository(testRepo);
      const updates = { name: 'Updated Name', description: 'Updated description' };
      
      const updatedRepo = await updateRepository(createdRepo.id, updates);
      
      expect(updatedRepo.name).toBe(updates.name);
      expect(updatedRepo.description).toBe(updates.description);
    });

    it('should fail when updating non-existent repository', async () => {
      const updates = { name: 'Updated Name' };
      await expect(updateRepository('nonexistent-id', updates))
        .rejects.toThrow('Repository not found');
    });
  });

  describe('deleteRepository()', () => {
    it('should delete existing repository', async () => {
      const createdRepo = await createRepository(testRepo);
      await deleteRepository(createdRepo.id);
      
      const foundRepo = await getRepository(createdRepo.id);
      expect(foundRepo).toBeNull();
    });

    it('should fail when deleting non-existent repository', async () => {
      await expect(deleteRepository('nonexistent-id'))
        .rejects.toThrow('Repository not found');
    });
  });
}); 