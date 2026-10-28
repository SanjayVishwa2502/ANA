package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"
)

// AuditRecord defines the structure for on-chain cryptographic metadata (Zero PHI)
type AuditRecord struct {
	TxID         string `json:"tx_id"`
	ActorID      string `json:"actor_id"`
	ActionType   string `json:"action_type"`
	TimestampUTC string `json:"timestamp_utc"`
	SHA256Hash   string `json:"sha256_hash"`
}

// MockWorldState simulates Hyperledger Fabric's key-value ledger state database
type MockWorldState struct {
	state map[string][]byte
}

func NewMockWorldState() *MockWorldState {
	return &MockWorldState{state: make(map[string][]byte)}
}

func (ws *MockWorldState) PutState(key string, value []byte) error {
	ws.state[key] = value
	return nil
}

func (ws *MockWorldState) GetState(key string) ([]byte, error) {
	val, exists := ws.state[key]
	if !exists {
		return nil, fmt.Errorf("Key %s not found on ledger", key)
	}
	return val, nil
}

// LogEvent records a new clinical audit record onto the chaincode ledger
func LogEvent(ws *MockWorldState, txID string, actorID string, actionType string, hashStr string) (*AuditRecord, error) {
	record := AuditRecord{
		TxID:         txID,
		ActorID:      actorID,
		ActionType:   actionType,
		TimestampUTC: time.Now().UTC().Format(time.RFC3339),
		SHA256Hash:   hashStr,
	}

	recordBytes, err := json.Marshal(record)
	if err != nil {
		return nil, fmt.Errorf("Failed to serialize audit record: %v", err)
	}

	err = ws.PutState(txID, recordBytes)
	if err != nil {
		return nil, fmt.Errorf("Failed to write to blockchain world state: %v", err)
	}

	return &record, nil
}

// VerifyEvent checks if an off-chain document matches the hash stored on the ledger
func VerifyEvent(ws *MockWorldState, txID string, offChainData string) (bool, string, error) {
	recordBytes, err := ws.GetState(txID)
	if err != nil {
		return false, "", err
	}

	var record AuditRecord
	err = json.Unmarshal(recordBytes, &record)
	if err != nil {
		return false, "", fmt.Errorf("Failed to unmarshal ledger record: %v", err)
	}

	// Compute SHA-256 hash of off-chain document
	hash := sha256.Sum256([]byte(offChainData))
	recomputedHash := hex.EncodeToString(hash[:])

	if recomputedHash == record.SHA256Hash {
		return true, record.SHA256Hash, nil
	}

	return false, record.SHA256Hash, nil
}

func main() {
	fmt.Println("==================================================================")
	fmt.Println("⛓️  Initializing Hyperledger Fabric Go Chaincode Audit Contract...")
	fmt.Println("==================================================================\n")

	ledger := NewMockWorldState()

	// Sample off-chain clinical note content
	authenticNote := `{"action":["Administered 0.4 mg sublingual nitroglycerin","Started 2 L oxygen"],"confidence_score":0.96,"data":["Acutely diaphoretic and tachypneic","Vitals: Sinus tachycardia at 135 bpm"],"requires_manual_flag":false,"response":["Initial evaluation logged"],"teaching":["Patient advised to remain still"]}`
	
	// Compute authentic SHA-256
	h := sha256.Sum256([]byte(authenticNote))
	authenticHash := hex.EncodeToString(h[:])

	txID := "tx_fabric_go_9941"
	actorID := "Nurse_Auth_8841"
	actionType := "DART_NOTE_APPROVED"

	fmt.Println("1. Executing Chaincode Function: LogEvent()...")
	record, err := LogEvent(ledger, txID, actorID, actionType, authenticHash)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	fmt.Printf("   [Chaincode Ledger Commit Success]\n")
	fmt.Printf("   TxID: %s | Actor: %s | Action: %s\n", record.TxID, record.ActorID, record.ActionType)
	fmt.Printf("   Anchored SHA-256 Hash: %s\n\n", record.SHA256Hash)

	fmt.Println("2. Executing Chaincode Function: VerifyEvent() [Authentic Note]...")
	valid, onChainHash, err := VerifyEvent(ledger, txID, authenticNote)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	if valid {
		fmt.Printf("   ✅ INTEGRITY VERIFIED: Off-chain payload matches on-chain hash (%s)\n\n", onChainHash[:16]+"...")
	}

	fmt.Println("3. Simulating Off-Chain Record Tampering & Running Verification...")
	tamperedNote := `{"action":["Administered 4.0 mg sublingual nitroglycerin","Started 2 L oxygen"],"confidence_score":0.96,"data":["Acutely diaphoretic and tachypneic","Vitals: Sinus tachycardia at 135 bpm"],"requires_manual_flag":false,"response":["Initial evaluation logged"],"teaching":["Patient advised to remain still"]}`

	validTamper, _, _ := VerifyEvent(ledger, txID, tamperedNote)
	if !validTamper {
		fmt.Println("   🚨 SECURITY ALERT: SHA-256 Mismatch Detected by Chaincode!")
		fmt.Println("   Off-chain clinical record has been tampered with post-approval!")
	}
	fmt.Println("\n==================================================================")
}