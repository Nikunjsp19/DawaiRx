package com.dawai.repository;

import com.dawai.document.UserDocument;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;

import java.util.Optional;

public interface UserRepository extends MongoRepository<UserDocument, String> {

    @Query("{ 'user_id' : ?0 }")
    Optional<UserDocument> findByUserId(String userId);

    @Query(value = "{ 'user_id' : ?0 }", exists = true)
    boolean existsByUserId(String userId);
}
