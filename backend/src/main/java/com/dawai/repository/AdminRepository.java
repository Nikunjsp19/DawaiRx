package com.dawai.repository;

import com.dawai.document.AdminDocument;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;

public interface AdminRepository extends MongoRepository<AdminDocument, String> {

    @Query(value = "{ 'user_id' : ?0 }", exists = true)
    boolean existsByUserId(String userId);
}
